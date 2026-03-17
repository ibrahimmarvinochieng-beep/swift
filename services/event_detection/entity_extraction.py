"""Named Entity Recognition using spaCy, plus geocoding and location disambiguation.

Extracts: locations (GPE, LOC), organizations (ORG), persons (PERSON),
facilities (FAC), dates (DATE). Geocodes with Nominatim. Disambiguates
multiple locations by specificity and geocoding confidence.
"""

from typing import Dict, List, Any, Optional
from utils.config_loader import get_settings
from utils.logger import logger

settings = get_settings()
_nlp = None

# Location specificity: more specific = higher rank (city > region > country)
LOCATION_SPECIFICITY = {
    "city": 3,
    "town": 3,
    "village": 2,
    "region": 2,
    "state": 2,
    "province": 2,
    "country": 1,
    "continent": 0,
}


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
            logger.info("spacy_model_loaded", model="en_core_web_sm")
        except OSError:
            logger.error("spacy_model_not_found_run: python -m spacy download en_core_web_sm")
            raise
    return _nlp


def _disambiguate_locations(locations: List[str], text: str) -> List[str]:
    """Rank locations by relevance: order in text, specificity, length.
    Returns ordered list with most relevant first.
    """
    if not locations or len(locations) <= 1:
        return locations

    text_lower = text.lower()
    scored: List[tuple] = []

    for loc in locations:
        loc_lower = loc.lower()
        pos = text_lower.find(loc_lower)
        order_score = 1.0 / (pos + 1) if pos >= 0 else 0.5

        spec_score = 1.0
        for keyword, rank in LOCATION_SPECIFICITY.items():
            if keyword in loc_lower:
                spec_score = rank / 3.0
                break

        length_score = min(len(loc.split()), 5) / 5.0
        total = 0.4 * order_score + 0.4 * spec_score + 0.2 * length_score
        scored.append((loc, total))

    scored.sort(key=lambda x: -x[1])
    return [loc for loc, _ in scored]


class EntityExtractor:
    LABEL_GROUPS = {
        "locations": {"GPE", "LOC"},
        "organizations": {"ORG"},
        "persons": {"PERSON"},
        "facilities": {"FAC"},
        "dates": {"DATE"},
        "events": {"EVENT"},
    }

    def __init__(self):
        self._geocoder = None

    def _get_geocoder(self):
        if self._geocoder is None:
            try:
                from geopy.geocoders import Nominatim
                self._geocoder = Nominatim(
                    user_agent="swift_event_platform",
                    timeout=10,
                )
            except Exception as e:
                logger.error("geocoder_init_failed", error=str(e))
        return self._geocoder

    def extract(self, text: str) -> Dict[str, List[str]]:
        if not text:
            return {}

        nlp = _get_nlp()
        doc = nlp(text[:5000])

        entities: Dict[str, List[str]] = {}
        for group_name, labels in self.LABEL_GROUPS.items():
            values = list({ent.text.strip() for ent in doc.ents if ent.label_ in labels})
            if values:
                entities[group_name] = values

        if entities.get("locations"):
            entities["locations"] = _disambiguate_locations(
                entities["locations"], text
            )

        logger.debug("entities_extracted", count=sum(len(v) for v in entities.values()))
        return entities

    def geocode(self, locations: List[str]) -> Dict[str, Any]:
        if not locations:
            return {}

        geocoder = self._get_geocoder()
        if geocoder is None:
            return {"location_name": locations[0] if locations else None}

        for loc_name in locations:
            try:
                result = geocoder.geocode(loc_name)
                if result:
                    return {
                        "location_name": loc_name,
                        "latitude": round(result.latitude, 6),
                        "longitude": round(result.longitude, 6),
                        "full_address": result.address,
                    }
            except Exception as e:
                logger.warning("geocode_failed", location=loc_name, error=str(e))

        return {"location_name": locations[0] if locations else None}


def extract_and_geocode(text: str) -> Dict[str, Any]:
    """Convenience: extract entities then geocode the first (disambiguated) location."""
    extractor = EntityExtractor()
    entities = extractor.extract(text)
    location_data = extractor.geocode(entities.get("locations", []))
    return {"entities": entities, "geo": location_data}
