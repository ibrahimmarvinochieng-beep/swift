"""Signal processor — runs one signal through the full detection pipeline.

    signal dict → filter → classify → extract entities → geocode
    → deduplicate → structure → EventRepository

Returns the structured event dict, or None if the signal was
filtered / not-an-event / duplicate.
Failed signals (exceptions) are pushed to the DLQ.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from collectors.signal_filter import filter_signal
from services.event_detection.classifier import EventClassifier
from services.event_detection.entity_extraction import EntityExtractor
from services.event_detection.language import prepare_text_for_classification
from services.event_detection.deduplication import EventDeduplicator
from services.event_detection.structuring import EventStructurer
from db.repository import event_repo
from ingestion.dlq import push as dlq_push
from utils.logger import logger

_classifier = EventClassifier()
_extractor = EntityExtractor()
_deduplicator = EventDeduplicator()
_structurer = EventStructurer()


def process_signal(signal: dict) -> Optional[dict]:
    """Push one raw signal through the full pipeline. Returns structured event or None."""

    try:
        return _process_signal_impl(signal)
    except Exception as e:
        dlq_push(signal, reason="processing_exception", error=str(e))
        logger.error("process_signal_failed", signal_id=signal.get("signal_id"), error=str(e))
        return None


def _process_signal_impl(signal: dict) -> Optional[dict]:
    """Inner implementation. Exceptions bubble to process_signal for DLQ."""
    text = signal.get("content", "")
    if not text:
        return None

    # ── 1. Filter ─────────────────────────────────────────────────
    passes, relevance = filter_signal(signal)
    if not passes:
        logger.debug("signal_filtered_out", signal_id=signal.get("signal_id"))
        return None

    # ── 2. Language + Classify ───────────────────────────────────
    text_for_clf, detected_lang = prepare_text_for_classification(text)
    classification = _classifier.classify(text_for_clf)
    if not classification["event_detected"]:
        logger.debug("signal_not_event", signal_id=signal.get("signal_id"))
        return None

    # ── 3. Entity extraction ──────────────────────────────────────
    try:
        entities = _extractor.extract(text)
        location_data = _extractor.geocode(entities.get("locations", []))
    except Exception:
        entities = {}
        location_data = {}

    # ── 4. Build raw event ────────────────────────────────────────
    event_id = str(uuid.uuid4())
    event_data = {
        "event_id": event_id,
        "event_type": classification["event_type"],
        "event_types": classification.get("event_types", [classification["event_type"]]),
        "title": classification.get("title", text[:120]),
        "description": text,
        "confidence_score": classification["confidence"],
        "entities": entities,
        "location": location_data.get("location_name"),
        "latitude": location_data.get("latitude"),
        "longitude": location_data.get("longitude"),
        "sources": [signal.get("source_name", "unknown")],
        "detected_lang": detected_lang,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # ── 5. Deduplicate ────────────────────────────────────────────
    is_dup, existing_id = _deduplicator.check(text, event_id)
    if is_dup:
        logger.info("duplicate_merged", new=event_id, into=existing_id)
        return None

    # ── 6. Structure + store ──────────────────────────────────────
    structured = _structurer.structure(event_data)
    event_repo.add_event(structured)

    logger.info(
        "event_created",
        event_id=structured["event_id"],
        type=structured["event_type"],
        severity=structured["severity"],
        location=structured.get("location"),
    )

    # ── 7. OpenClaw webhook (optional) ───────────────────────────────
    _notify_openclaw(structured)

    # ── 8. Impact Prediction (optional) ──────────────────────────────
    _run_impact_prediction(structured)

    return structured


def _run_impact_prediction(event: dict) -> None:
    """Run impact prediction for new event. Non-blocking, best-effort."""
    try:
        from services.impact_prediction.engine import predict_impacts
        impacts = predict_impacts(event)
        if impacts:
            logger.info("impact_prediction_complete", event_id=event.get("event_id"), impacts=len(impacts))
    except Exception as e:
        logger.warning("impact_prediction_failed", event_id=event.get("event_id"), error=str(e))


def _notify_openclaw(event: dict) -> None:
    """Push high-severity events to OpenClaw webhook if configured."""
    import os
    url = os.environ.get("OPENCLAW_WEBHOOK_URL") or ""
    token = os.environ.get("OPENCLAW_WEBHOOK_TOKEN") or ""
    if not url or not token:
        return
    if event.get("severity", 0) < 3:
        return
    try:
        import httpx
        title = event.get("title", "Event")
        etype = event.get("event_type", "unknown")
        severity = event.get("severity", 0)
        location = event.get("location", "")
        msg = f"🚨 **{title}**\nType: {etype} | Severity: {severity}"
        if location:
            msg += f"\nLocation: {location}"
        payload = {"message": f"[Swift Event]\n\n{msg}", "name": "Swift", "wakeMode": "now", "deliver": True}
        with httpx.Client(timeout=10.0) as client:
            client.post(url, json=payload, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    except Exception as e:
        logger.debug("openclaw_webhook_failed", error=str(e))


def get_deduplicator() -> EventDeduplicator:
    return _deduplicator
