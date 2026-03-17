"""Worker that consumes filtered signals, runs event detection, entity extraction,
deduplication, and structuring, then publishes structured events."""

import uuid
from datetime import datetime, timezone

from utils.logger import logger
from services.event_detection.classifier import EventClassifier
from services.event_detection.entity_extraction import EntityExtractor
from services.event_detection.deduplication import EventDeduplicator
from services.event_detection.structuring import EventStructurer
from streaming.consumer import consume_loop
from streaming.producer import publish_structured_event, TOPICS


classifier = EventClassifier()
extractor = EntityExtractor()
deduplicator = EventDeduplicator()
structurer = EventStructurer()


def process_signal(signal: dict) -> None:
    text = signal.get("content", "")
    if not text:
        return

    classification = classifier.classify(text)
    if not classification["event_detected"]:
        logger.debug("signal_not_event", signal_id=signal.get("signal_id"))
        return

    entities = extractor.extract(text)
    location_data = extractor.geocode(entities.get("locations", []))

    event_data = {
        "event_id": str(uuid.uuid4()),
        "event_type": classification["event_type"],
        "title": classification.get("title", text[:120]),
        "description": text,
        "confidence_score": classification["confidence"],
        "entities": entities,
        "location": location_data.get("location_name"),
        "latitude": location_data.get("latitude"),
        "longitude": location_data.get("longitude"),
        "sources": [signal.get("source_name", "unknown")],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    is_duplicate, existing_id = deduplicator.check(text, event_data["event_id"])
    if is_duplicate:
        logger.info("event_deduplicated", new_id=event_data["event_id"], merged_into=existing_id)
        return

    structured = structurer.structure(event_data)
    try:
        publish_structured_event(structured)
    except Exception as e:
        logger.warning("structured_event_publish_failed", error=str(e))

    logger.info(
        "event_structured",
        event_id=structured["event_id"],
        event_type=structured["event_type"],
        severity=structured.get("severity"),
    )


if __name__ == "__main__":
    logger.info("event_detection_worker_starting")
    consume_loop(
        topic=TOPICS["filtered_signals"],
        group_id="event-detection-group",
        handler=process_signal,
    )
