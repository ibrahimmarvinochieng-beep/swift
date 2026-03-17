"""Intelligence service — For You recommendations, monitoring, alerts, suggested actions.

Uses user profile (connected apps, preferences) and event repository
to produce personalized feeds and alerts.
"""

from typing import Dict, List, Optional, Tuple

from db.repository import event_repo
from db.user_profile_store import get_user_profile_store
from utils.logger import logger

# Topic mapping: event_type -> display topic
EVENT_TYPE_TO_TOPIC = {
    "natural_disaster": "Disasters",
    "transport_disruption": "Transport",
    "infrastructure_failure": "Infrastructure",
    "public_health": "Health",
    "security_incident": "Security",
    "political_event": "Policy",
    "economic_event": "Markets",
    "environmental_hazard": "Weather",
    "technology_incident": "Technology",
    "social_unrest": "Society",
}

# Region hints from location (simple substring matching)
REGION_KEYWORDS = {
    "North America": ["usa", "united states", "canada", "mexico", "new york", "california", "san francisco", "miami", "washington"],
    "South America": ["chile", "brazil", "argentina", "colombia", "peru", "santiago", "sao paulo"],
    "Europe": ["europe", "eu", "uk", "germany", "france", "brussels", "london"],
    "Asia": ["asia", "china", "japan", "india", "singapore", "tokyo"],
    "Africa": ["africa", "nigeria", "south africa", "kenya"],
}


def _derive_topic(event: dict) -> str:
    """Derive display topic from event_type."""
    etype = event.get("event_type", "political_event")
    return EVENT_TYPE_TO_TOPIC.get(etype, "Policy")


def _derive_region(event: dict) -> str:
    """Derive region from location."""
    loc = (event.get("location") or "").lower()
    if not loc:
        return "unknown"
    for region, keywords in REGION_KEYWORDS.items():
        if any(kw in loc for kw in keywords):
            return region
    return "unknown"


def _enrich_event(event: dict) -> dict:
    """Add topic and region for display/filtering."""
    out = dict(event)
    out["topic"] = _derive_topic(event)
    out["region"] = _derive_region(event)
    return out


def _generate_suggested_actions(event: dict, alert_type: str = "development") -> List[str]:
    """Generate suggested actions based on event type and content."""
    etype = event.get("event_type", "")
    title = (event.get("title") or "").lower()
    actions = []

    if "natural_disaster" in etype or "earthquake" in title or "storm" in title:
        actions.extend(["Check travel advisories", "Contact local contacts"])
    if "economic" in etype or "market" in title:
        actions.extend(["Review portfolio positions", "Check market impact"])
    if "transport" in etype or "flight" in title:
        actions.extend(["Check flight status", "Rebook if needed"])
    if "health" in etype or "outbreak" in title:
        actions.extend(["Check health advisories", "Review travel plans"])
    if "security" in etype or "attack" in title:
        actions.extend(["Verify safety of affected areas", "Contact emergency contacts"])

    if not actions:
        actions = ["Review event details", "Share with relevant team"]
    return actions[:4]


class IntelligenceService:
    """Service for personalized recommendations and monitoring."""

    def __init__(self):
        self._store = get_user_profile_store()

    def get_recommended_events(
        self,
        user_id: str,
        topic: Optional[str] = None,
        region: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[dict], int]:
        """For You feed: events recommended based on user profile."""
        profile = self._store.get_profile(user_id)
        all_events, total = event_repo.list_events(
            search=search,
            page=1,
            page_size=1000,
        )

        # Enrich with topic/region
        enriched = [_enrich_event(e) for e in all_events]

        # Apply topic filter
        if topic and topic != "All topics":
            enriched = [e for e in enriched if e.get("topic") == topic]
        if region and region != "All regions":
            enriched = [e for e in enriched if e.get("region") == region]

        # Score by preference match (simple: boost if user has topic/region in preferences)
        prefs_topics = set(profile.get("preferred_topics", []))
        prefs_regions = set(profile.get("preferred_regions", []))
        connected = set(profile.get("connected_apps", []))

        def score(e: dict) -> float:
            s = 0.5  # base
            if e.get("topic") in prefs_topics:
                s += 0.3
            if e.get("region") in prefs_regions:
                s += 0.2
            if connected:
                s += 0.1  # slight boost for engaged users
            return s

        enriched.sort(key=lambda e: (score(e), e.get("created_at", "")), reverse=True)
        total = len(enriched)
        start = (page - 1) * page_size
        page_events = enriched[start : start + page_size]

        return page_events, total

    def get_monitored_events(
        self,
        user_id: str,
        topic: Optional[str] = None,
        region: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[dict], int]:
        """Monitoring feed: events the user is following."""
        monitored_ids = self._store.get_monitored_event_ids(user_id)
        if not monitored_ids:
            return [], 0

        all_events, _ = event_repo.list_events(page=1, page_size=1000)
        monitored = [e for e in all_events if e.get("event_id") in monitored_ids]
        enriched = [_enrich_event(e) for e in monitored]

        if topic and topic != "All topics":
            enriched = [e for e in enriched if e.get("topic") == topic]
        if region and region != "All regions":
            enriched = [e for e in enriched if e.get("region") == region]
        if search:
            q = search.lower()
            enriched = [
                e for e in enriched
                if q in (e.get("title") or "").lower() or q in (e.get("description") or "").lower()
            ]

        enriched.sort(key=lambda e: e.get("created_at", ""), reverse=True)
        total = len(enriched)
        start = (page - 1) * page_size
        return enriched[start : start + page_size], total

    def toggle_monitoring(self, user_id: str, event_id: str) -> bool:
        """Toggle monitoring: add if not monitoring, remove if monitoring."""
        monitored = self._store.get_monitored_event_ids(user_id)
        if event_id in monitored:
            return self._store.remove_monitoring(user_id, event_id)
        return self._store.add_monitoring(user_id, event_id)

    def is_monitoring(self, user_id: str, event_id: str) -> bool:
        return event_id in self._store.get_monitored_event_ids(user_id)

    def get_alerts(
        self,
        user_id: str,
        limit: int = 20,
        unread_only: bool = False,
    ) -> List[dict]:
        """Get alerts for user with suggested actions."""
        return self._store.get_alerts(user_id, limit=limit, unread_only=unread_only)

    def create_development_alert(
        self,
        user_id: str,
        event: dict,
        development_title: str,
        development_body: str,
    ) -> Optional[str]:
        """Create an alert when there's a development in a monitored event."""
        actions = _generate_suggested_actions(event, "development")
        return self._store.add_alert(
            user_id=user_id,
            event_id=event.get("event_id", ""),
            alert_type="development",
            title=development_title,
            body=development_body,
            suggested_actions=actions,
        )

    def update_profile(
        self,
        user_id: str,
        connected_apps: Optional[List[str]] = None,
        preferred_topics: Optional[List[str]] = None,
        preferred_regions: Optional[List[str]] = None,
    ) -> dict:
        """Update user profile."""
        return self._store.update_profile(
            user_id=user_id,
            connected_apps=connected_apps,
            preferred_topics=preferred_topics,
            preferred_regions=preferred_regions,
        )
