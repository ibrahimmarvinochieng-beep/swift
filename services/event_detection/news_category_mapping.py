"""Mapping from HuffPost news categories to EVENT_TYPES for classifier integration."""

# News category → event_type (for pipeline compatibility)
NEWS_CATEGORY_TO_EVENT_TYPE = {
    "U.S. NEWS": "political_event",
    "WORLD NEWS": "political_event",
    "POLITICS": "political_event",
    "ENVIRONMENT": "environmental_hazard",
    "TECH": "technology_incident",
    "EDUCATION": "political_event",
    "SPORTS": "political_event",  # or add sports_event if desired
    "ENTERTAINMENT": "political_event",
    "CULTURE & ARTS": "political_event",
    "COMEDY": "political_event",
    "PARENTING": "political_event",
    "WEIRD NEWS": "political_event",
    "HEALTHY LIVING": "public_health",
    "STYLE": "political_event",
    "BUSINESS": "economic_event",
    "SCIENCE": "political_event",
    "CRIME": "security_incident",
    "MEDIA": "political_event",
    "RELIGION": "political_event",
    "FOOD & DRINK": "political_event",
    "HOME & LIVING": "political_event",
    "WOMEN": "political_event",
    "BLACK VOICES": "political_event",
    "LATINO VOICES": "political_event",
    "QUEER VOICES": "political_event",
    "IMPACT": "political_event",
    "WEDDINGS": "political_event",
    "DIVORCE": "political_event",
    "MONEY": "economic_event",
    "ARTS": "political_event",
    "COLLEGE": "political_event",
    "GOOD NEWS": "political_event",
    "GREEN": "environmental_hazard",
    "TASTE": "political_event",
    "THE WORLDPOST": "political_event",
    "FIFTY": "political_event",
    "ARTS & CULTURE": "political_event",
}

DEFAULT_EVENT_TYPE = "political_event"


def news_category_to_event_type(category: str) -> str:
    """Map a news category to an EVENT_TYPE for the pipeline."""
    return NEWS_CATEGORY_TO_EVENT_TYPE.get(
        category.upper().strip(),
        DEFAULT_EVENT_TYPE,
    )
