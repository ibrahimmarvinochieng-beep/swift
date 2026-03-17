"""Converts raw detected events into structured event objects for storage and streaming.

Assigns severity levels based on event type and content analysis,
validates required fields, and produces the final event schema.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from utils.logger import logger

SEVERITY_MAP = {
    "natural_disaster": 5,
    "security_incident": 5,
    "public_health": 4,
    "infrastructure_failure": 4,
    "transport_disruption": 3,
    "social_unrest": 4,
    "environmental_hazard": 3,
    "economic_event": 3,
    "political_event": 2,
    "technology_incident": 3,
}

HIGH_SEVERITY_KEYWORDS = [
    "death", "killed", "fatal", "catastrophic", "mass casualty",
    "state of emergency", "evacuation", "critical", "destroyed",
    "collapsed", "magnitude 7", "magnitude 8", "category 5",
]


class EventStructurer:
    def _compute_severity(self, event_type: str, text: str) -> int:
        base = SEVERITY_MAP.get(event_type, 2)
        text_lower = text.lower() if text else ""

        boost = sum(1 for kw in HIGH_SEVERITY_KEYWORDS if kw in text_lower)
        severity = min(base + boost, 5)
        return severity

    def structure(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        event_type = raw_event.get("event_type", "unknown")
        description = raw_event.get("description", "")

        event_types = raw_event.get("event_types", [event_type])
        if event_type and event_type not in event_types:
            event_types = [event_type] + [t for t in event_types if t != event_type]

        structured = {
            "event_id": raw_event.get("event_id", str(uuid.uuid4())),
            "event_type": event_type,
            "event_types": event_types[:5],
            "title": raw_event.get("title", description[:120]).strip(),
            "description": description,
            "location": raw_event.get("location"),
            "latitude": raw_event.get("latitude"),
            "longitude": raw_event.get("longitude"),
            "severity": self._compute_severity(event_type, description),
            "confidence_score": raw_event.get("confidence_score", 0.0),
            "sources": raw_event.get("sources", []),
            "entities": raw_event.get("entities", {}),
            "timestamp": raw_event.get(
                "timestamp", datetime.now(timezone.utc).isoformat()
            ),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(
            "event_structured",
            event_id=structured["event_id"],
            event_type=structured["event_type"],
            severity=structured["severity"],
            location=structured["location"],
        )
        return structured

    def validate(self, event: Dict[str, Any]) -> bool:
        required = ["event_id", "event_type", "title", "confidence_score"]
        for field in required:
            if not event.get(field):
                logger.warning("event_validation_failed", missing_field=field)
                return False

        if not (0 <= event.get("confidence_score", 0) <= 1):
            return False
        if not (1 <= event.get("severity", 0) <= 5):
            return False
        return True
