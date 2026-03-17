from typing import List
import httpx
from collectors.base_collector import BaseCollector
from utils.config_loader import get_settings
from utils.logger import logger
from utils.security_utils import sanitize_input

settings = get_settings()

TWITTER_SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"

DEFAULT_QUERIES = [
    "breaking news disaster",
    "earthquake OR tsunami OR flood OR hurricane",
    "explosion OR attack OR emergency",
    "outbreak OR pandemic OR epidemic",
    "infrastructure failure OR power outage",
]


class SocialMediaCollector(BaseCollector):
    name = "social_media"

    def __init__(self, queries: List[str] = None):
        self.queries = queries or DEFAULT_QUERIES

    async def collect(self) -> List[dict]:
        if not settings.twitter_bearer_token:
            logger.warning("twitter_bearer_token_not_set")
            return []

        signals = []
        headers = {"Authorization": f"Bearer {settings.twitter_bearer_token}"}

        async with httpx.AsyncClient(timeout=15.0) as client:
            for query in self.queries:
                try:
                    response = await client.get(
                        TWITTER_SEARCH_URL,
                        headers=headers,
                        params={
                            "query": f"{query} -is:retweet lang:en",
                            "max_results": 20,
                            "tweet.fields": "created_at,author_id,geo,public_metrics",
                        },
                    )
                    response.raise_for_status()
                    data = response.json()

                    for tweet in data.get("data", []):
                        text = sanitize_input(tweet.get("text", ""))
                        if len(text) < 20:
                            continue

                        metrics = tweet.get("public_metrics", {})
                        signal = self.normalize_signal(
                            content=text,
                            source_type="social_media",
                            source_name="twitter",
                            url=f"https://twitter.com/i/web/status/{tweet['id']}",
                            metadata={
                                "tweet_id": tweet["id"],
                                "author_id": tweet.get("author_id"),
                                "created_at": tweet.get("created_at"),
                                "retweets": metrics.get("retweet_count", 0),
                                "likes": metrics.get("like_count", 0),
                                "query": query,
                            },
                        )
                        signals.append(signal)

                    logger.info("social_media_fetched", query=query, count=len(data.get("data", [])))

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:
                        logger.warning("twitter_rate_limited", query=query)
                    else:
                        logger.error("twitter_request_failed", query=query, error=str(e))
                except httpx.HTTPError as e:
                    logger.error("twitter_request_failed", query=query, error=str(e))

        return signals
