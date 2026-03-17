"""AI-powered event classification — multi-model ensemble with calibration.

Supports:
  - Fine-tuned news classifier (trained on News_Category_Dataset)
  - Multi-model ensemble: BART + DistilBERT + keyword voting
  - Multi-label classification (multiple event types per signal)
  - Confidence calibration (temperature scaling)
  - GPU inference when CUDA available
  - ONNX path (optional, when model exported)
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from utils.config_loader import get_settings
from utils.logger import logger

settings = get_settings()

EVENT_TYPES = [
    "natural_disaster",
    "transport_disruption",
    "infrastructure_failure",
    "public_health",
    "security_incident",
    "political_event",
    "economic_event",
    "environmental_hazard",
    "technology_incident",
    "social_unrest",
]

KEYWORD_MAP = {
    "natural_disaster": [
        "earthquake", "flood", "tsunami", "hurricane", "tornado", "volcano",
        "landslide", "wildfire", "cyclone", "typhoon", "drought",
    ],
    "transport_disruption": [
        "flight delay", "airport", "train delay", "road closure", "crash",
        "derailment", "traffic", "grounded", "cancellation",
    ],
    "infrastructure_failure": [
        "power outage", "blackout", "water supply", "bridge collapse",
        "building collapse", "dam", "pipeline", "grid failure",
    ],
    "public_health": [
        "outbreak", "pandemic", "epidemic", "virus", "infection", "hospital",
        "vaccine", "quarantine", "contamination", "disease",
    ],
    "security_incident": [
        "attack", "shooting", "bomb", "explosion", "hostage", "terrorism",
        "assassination", "breach", "cyberattack",
    ],
    "political_event": [
        "election", "coup", "sanctions", "legislation", "treaty", "summit",
        "diplomatic", "embargo", "impeachment",
    ],
    "economic_event": [
        "market crash", "recession", "inflation", "bankruptcy", "stock",
        "currency", "trade war", "default", "bailout",
    ],
    "environmental_hazard": [
        "oil spill", "pollution", "toxic", "chemical leak", "radiation",
        "deforestation", "coral bleaching",
    ],
    "technology_incident": [
        "data breach", "hack", "ransomware", "outage", "server down",
        "vulnerability", "zero-day",
    ],
    "social_unrest": [
        "protest", "riot", "demonstration", "strike", "civil unrest",
        "looting", "martial law",
    ],
}


def _get_device() -> int:
    """Return CUDA device id (0) if available, else -1."""
    try:
        import torch
        return 0 if torch.cuda.is_available() else -1
    except ImportError:
        return -1


def _calibrate_confidence(raw_score: float, temperature: float = 1.0) -> float:
    """Temperature scaling: calibrated = raw^(1/T). T>1 flattens, T<1 sharpens."""
    if temperature <= 0:
        return raw_score
    return max(0.0, min(1.0, raw_score ** (1.0 / temperature)))


class EventClassifier:
    def __init__(self):
        self._bart_pipeline = None
        self._distil_pipeline = None
        self._finetuned_pipeline = None
        self._load_attempted = False
        self._device = _get_device()

    def _load_finetuned(self) -> bool:
        """Load fine-tuned news classifier if path is set and exists."""
        path = getattr(settings, "classifier_finetuned_model_path", "") or ""
        if not path or not Path(path).is_dir():
            return False
        try:
            from transformers import pipeline
            self._finetuned_pipeline = pipeline(
                "text-classification",
                model=path,
                device=self._device,
                top_k=5,
            )
            logger.info("classifier_loaded", model="finetuned-news", path=path)
            return True
        except Exception as e:
            logger.warning("finetuned_model_load_failed", path=path, error=str(e))
            return False

    def _classify_finetuned(self, text: str) -> Optional[Dict[str, Any]]:
        """Run fine-tuned news classifier; map category to event_type."""
        if self._finetuned_pipeline is None:
            return None
        try:
            from services.event_detection.news_category_mapping import (
                news_category_to_event_type,
            )
            result = self._finetuned_pipeline(text[:512], truncation=True)
            if isinstance(result, list) and result:
                top = result[0] if isinstance(result[0], dict) else {}
                all_items = result
            else:
                top = {}
                all_items = []
            label = top.get("label", "")
            score = float(top.get("score", 0.0))
            calib_temp = getattr(settings, "classifier_confidence_temperature", 1.0)
            calibrated = _calibrate_confidence(score, calib_temp)
            event_type = news_category_to_event_type(label)
            return {
                "event_detected": calibrated >= settings.event_confidence_threshold,
                "event_type": event_type,
                "event_types": [event_type],
                "confidence": round(calibrated, 3),
                "method": "finetuned",
                "news_category": label,
                "all_scores": {r.get("label", ""): r.get("score", 0) for r in all_items} if all_items else {},
                "title": text[:120].strip(),
            }
        except Exception as e:
            logger.debug("finetuned_classify_failed", error=str(e))
            return None

    def _load_models(self):
        if self._load_attempted:
            return
        self._load_attempted = True

        self._load_finetuned()

        try:
            from transformers import pipeline
            device = self._device
            use_fast = getattr(settings, "classifier_use_fast_model", True)

            if use_fast:
                try:
                    self._distil_pipeline = pipeline(
                        "zero-shot-classification",
                        model="typeform/distilbert-base-uncased-mnli",
                        device=device,
                    )
                    logger.info("classifier_loaded", model="distilbert-mnli", device=device)
                except Exception as e:
                    logger.warning("distilbert_load_failed", error=str(e))

            if self._distil_pipeline is None:
                self._bart_pipeline = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli",
                    device=device,
                )
                logger.info("classifier_loaded", model="bart-large-mnli", device=device)
        except Exception as e:
            logger.warning("classifier_model_unavailable", error=str(e))

    def _keyword_classify(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        scores: Dict[str, float] = {
            et: 0.0 for et in EVENT_TYPES
        }

        for event_type, keywords in KEYWORD_MAP.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            scores[event_type] = min(matches / 2.0, 1.0)

        sorted_types = sorted(scores.items(), key=lambda x: -x[1])
        best_type = sorted_types[0][0]
        best_score = sorted_types[0][1]
        detected = best_score >= 0.3

        multi_labels = [
            (t, s) for t, s in sorted_types if s >= 0.2
        ][:5]

        return {
            "event_detected": detected,
            "event_type": best_type if detected else None,
            "event_types": [t for t, _ in multi_labels] if detected else [],
            "confidence": round(best_score, 3),
            "all_scores": dict(multi_labels),
            "method": "keyword",
            "title": text[:120].strip(),
        }

    def _ensemble(self, zs_result: Optional[Dict], kw_result: Dict) -> Dict[str, Any]:
        """Combine zero-shot and keyword results with weighted voting."""
        multi_label = getattr(settings, "classifier_multi_label", False)
        calib_temp = getattr(settings, "classifier_confidence_temperature", 1.0)

        if zs_result is None:
            conf = _calibrate_confidence(kw_result["confidence"], calib_temp)
            kw_result["confidence"] = round(conf, 3)
            return kw_result

        zs_label = zs_result["labels"][0]
        zs_score = zs_result["scores"][0]
        kw_label = kw_result["event_type"]
        kw_score = kw_result["confidence"]

        combined_score = 0.5 * zs_score + 0.5 * kw_score
        if zs_label == kw_label:
            combined_score = min(combined_score + 0.1, 1.0)

        calibrated = _calibrate_confidence(combined_score, calib_temp)

        event_types = [zs_label]
        if multi_label:
            for label, score in zs_result.get("all_scores", {}).items():
                if score >= 0.3 and label not in event_types:
                    event_types.append(label)
            for t in kw_result.get("event_types", []):
                if t not in event_types:
                    event_types.append(t)

        return {
            "event_detected": calibrated >= settings.event_confidence_threshold or kw_result["event_detected"],
            "event_type": zs_label if zs_score >= kw_score else kw_label,
            "event_types": event_types[:3] if multi_label else [zs_label],
            "confidence": round(calibrated, 3),
            "all_scores": zs_result.get("all_scores", {}),
            "method": "ensemble",
            "title": kw_result.get("title", ""),
        }

    def classify(self, text: str) -> Dict[str, Any]:
        if not text or len(text.strip()) < 20:
            return {"event_detected": False, "event_type": None, "confidence": 0.0, "event_types": []}

        self._load_models()

        # Prefer fine-tuned model when available
        ft_result = self._classify_finetuned(text)
        if ft_result is not None and ft_result.get("event_detected"):
            return ft_result
        if ft_result is not None and ft_result.get("confidence", 0) >= 0.5:
            return ft_result

        zs_result = None
        pipeline = self._distil_pipeline or self._bart_pipeline
        multi_label = getattr(settings, "classifier_multi_label", False)

        if pipeline is not None:
            try:
                result = pipeline(
                    text[:512],
                    EVENT_TYPES,
                    multi_label=multi_label,
                )
                top_label = result["labels"][0]
                top_score = result["scores"][0]
                calib_temp = getattr(settings, "classifier_confidence_temperature", 1.0)
                calibrated = _calibrate_confidence(top_score, calib_temp)

                if calibrated >= settings.event_confidence_threshold:
                    event_types = result["labels"][:3] if multi_label else [top_label]
                    return {
                        "event_detected": True,
                        "event_type": top_label,
                        "event_types": event_types,
                        "confidence": round(calibrated, 3),
                        "method": "zero-shot",
                        "all_scores": dict(zip(result["labels"][:5], result["scores"][:5])),
                        "title": text[:120].strip(),
                    }
                zs_result = {
                    "labels": result["labels"],
                    "scores": result["scores"],
                    "all_scores": dict(zip(result["labels"][:5], result["scores"][:5])),
                }
            except Exception as e:
                logger.error("classifier_inference_failed", error=str(e))

        kw = self._keyword_classify(text)
        return self._ensemble(zs_result, kw)
