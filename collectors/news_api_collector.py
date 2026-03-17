from typing import List
import httpx
from collectors.base_collector import BaseCollector
from utils.config_loader import get_settings
from utils.logger import logger
from utils.security_utils import sanitize_input

settings = get_settings()

NEWS_API_URL = "https://newsapi.org/v2/top-headlines"


class NewsAPICollector(BaseCollector):
    name = "news_api"

    def __init__(self, categories: List[str] = None, country: str = "us"):
        self.categories = categories or ["general", "technology", "health", "science"]
        self.country = country

    async def collect(self) -> List[dict]:
        if not settings.news_api_key:
            logger.warning("news_api_key_not_set")
            return []

        signals = []
        async with httpx.AsyncClient(timeout=15.0) as client:
            for category in self.categories:
                try:
                    response = await client.get(
                        NEWS_API_URL,
                        params={
                            "apiKey": settings.news_api_key,
                            "country": self.country,
                            "category": category,
                            "pageSize": 20,
                        },
                    )
                    response.raise_for_status()
                    data = response.json()

                    for article in data.get("articles", []):
                        title = article.get("title", "")
                        description = article.get("description", "")
                        content = f"{title}. {description}"
                        content = sanitize_input(content)

                        if not content.strip() or len(content) < 20:
                            continue

                        signal = self.normalize_signal(
                            content=content,
                            source_type="news_api",
                            source_name=article.get("source", {}).get("name", "unknown"),
                            url=article.get("url", ""),
                            metadata={
                                "category": category,
                                "author": article.get("author"),
                                "image_url": article.get("urlToImage"),
                            },
                            published_at=article.get("publishedAt"),
                        )
                        signals.append(signal)

                    logger.info(
                        "news_api_fetched",
                        category=category,
                        article_count=len(data.get("articles", [])),
                    )
                except httpx.HTTPError as e:
                    logger.error("news_api_request_failed", category=category, error=str(e))

        return signals
