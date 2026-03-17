from typing import List
import feedparser
import httpx
from collectors.base_collector import BaseCollector
from utils.logger import logger
from utils.security_utils import sanitize_input

DEFAULT_FEEDS = [
    {"name": "Reuters World", "url": "https://feeds.reuters.com/reuters/worldNews"},
    {"name": "BBC News", "url": "http://feeds.bbci.co.uk/news/rss.xml"},
    {"name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml"},
    {"name": "AP News", "url": "https://rsshub.app/apnews/topics/apf-topnews"},
    {"name": "GDACS Alerts", "url": "https://www.gdacs.org/xml/rss.xml"},
]


class RSSCollector(BaseCollector):
    name = "rss"

    def __init__(self, feeds: List[dict] = None):
        self.feeds = feeds or DEFAULT_FEEDS

    async def collect(self) -> List[dict]:
        signals = []
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            for feed_info in self.feeds:
                try:
                    response = await client.get(feed_info["url"])
                    response.raise_for_status()
                    parsed = feedparser.parse(response.text)

                    for entry in parsed.entries[:20]:
                        title = getattr(entry, "title", "")
                        summary = getattr(entry, "summary", "")
                        content = sanitize_input(f"{title}. {summary}")

                        if len(content) < 20:
                            continue

                        signal = self.normalize_signal(
                            content=content,
                            source_type="rss",
                            source_name=feed_info["name"],
                            url=getattr(entry, "link", ""),
                            metadata={"feed_url": feed_info["url"]},
                            published_at=getattr(entry, "published", None) or getattr(entry, "updated", None),
                        )
                        signals.append(signal)

                    logger.info(
                        "rss_fetched",
                        feed=feed_info["name"],
                        entry_count=len(parsed.entries),
                    )
                except Exception as e:
                    logger.error("rss_fetch_failed", feed=feed_info["name"], error=str(e))

        return signals
