from typing import List
import httpx
from collectors.base_collector import BaseCollector
from utils.config_loader import get_settings
from utils.logger import logger

settings = get_settings()

OPENWEATHER_ALERTS_URL = "https://api.openweathermap.org/data/2.5/onecall"

MONITORED_LOCATIONS = [
    {"name": "New York", "lat": 40.7128, "lon": -74.0060},
    {"name": "London", "lat": 51.5074, "lon": -0.1278},
    {"name": "Dubai", "lat": 25.2048, "lon": 55.2708},
    {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503},
    {"name": "Lagos", "lat": 6.5244, "lon": 3.3792},
    {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
    {"name": "São Paulo", "lat": -23.5505, "lon": -46.6333},
    {"name": "Nairobi", "lat": -1.2921, "lon": 36.8219},
]


class WeatherAPICollector(BaseCollector):
    name = "weather_api"

    def __init__(self, locations: List[dict] = None):
        self.locations = locations or MONITORED_LOCATIONS

    async def collect(self) -> List[dict]:
        if not settings.weather_api_key:
            logger.warning("weather_api_key_not_set")
            return []

        signals = []
        async with httpx.AsyncClient(timeout=15.0) as client:
            for loc in self.locations:
                try:
                    response = await client.get(
                        OPENWEATHER_ALERTS_URL,
                        params={
                            "lat": loc["lat"],
                            "lon": loc["lon"],
                            "appid": settings.weather_api_key,
                            "exclude": "minutely,hourly,daily",
                        },
                    )
                    response.raise_for_status()
                    data = response.json()

                    for alert in data.get("alerts", []):
                        content = (
                            f"Weather alert in {loc['name']}: "
                            f"{alert.get('event', 'Unknown')}. "
                            f"{alert.get('description', '')}"
                        )

                        signal = self.normalize_signal(
                            content=content,
                            source_type="weather_api",
                            source_name="openweathermap",
                            metadata={
                                "location_name": loc["name"],
                                "latitude": loc["lat"],
                                "longitude": loc["lon"],
                                "alert_event": alert.get("event"),
                                "sender": alert.get("sender_name"),
                                "start": alert.get("start"),
                                "end": alert.get("end"),
                            },
                            published_at=alert.get("start") or alert.get("end"),
                        )
                        signals.append(signal)

                    logger.info(
                        "weather_fetched",
                        location=loc["name"],
                        alert_count=len(data.get("alerts", [])),
                    )
                except httpx.HTTPError as e:
                    logger.error("weather_request_failed", location=loc["name"], error=str(e))

        return signals
