"""Pipeline orchestrator — runs collectors + processing in a background loop.

Works locally without Kafka or Redis.  Designed to be started as a
background asyncio task inside the same process as the FastAPI server
(via `run_local.py`) or as a standalone worker.

Flow per cycle:
  1. Run every registered collector
  2. Filter, classify, extract, dedup, structure each signal
  3. Store accepted events in EventRepository
  4. Log stats
  5. Sleep and repeat
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List

from collectors.base_collector import BaseCollector
from collectors.demo_collector import DemoCollector
from collectors.news_api_collector import NewsAPICollector
from collectors.rss_collector import RSSCollector
from collectors.weather_api_collector import WeatherAPICollector
from collectors.signal_filter import filter_signals
from ingestion.source_rate_limiter import get_source_rate_limiter
from pipeline.processor import process_signal
from db.repository import event_repo
from utils.config_loader import get_settings
from utils.logger import logger

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="pipeline")

settings = get_settings()


def build_collectors() -> List[BaseCollector]:
    """Instantiate all available collectors.  Demo collector is always
    included so the platform works with zero API keys."""
    collectors: List[BaseCollector] = [DemoCollector(batch_size=5)]

    if settings.news_api_key:
        collectors.append(NewsAPICollector())
    if settings.twitter_bearer_token:
        from collectors.social_media_collector import SocialMediaCollector
        collectors.append(SocialMediaCollector())
    if settings.weather_api_key:
        collectors.append(WeatherAPICollector())

    collectors.append(RSSCollector())
    return collectors


async def run_pipeline_cycle(collectors: List[BaseCollector]) -> dict:
    """Execute one full ingestion cycle. Returns cycle stats."""
    raw_signals: list = []

    for collector in collectors:
        try:
            signals = await collector.safe_collect()
            raw_signals.extend(signals)
            logger.info("collector_done", name=collector.name, signals=len(signals))
        except Exception as e:
            logger.error("collector_failed", name=collector.name, error=str(e))

    filtered = filter_signals(raw_signals)

    source_limiter = get_source_rate_limiter()
    rate_limited: list = []
    for signal in filtered:
        source = signal.get("source_name", "unknown")
        if source_limiter.allow(source):
            rate_limited.append(signal)
        else:
            logger.debug("source_rate_limited", source=source)

    created = 0
    duplicates = 0
    rejected = len(raw_signals) - len(filtered) + (len(filtered) - len(rate_limited))

    loop = asyncio.get_event_loop()
    for signal in rate_limited:
        result = await loop.run_in_executor(_executor, process_signal, signal)
        if result:
            created += 1
        else:
            duplicates += 1

    event_repo.record_ingestion(
        filtered=len(filtered), rejected=rejected, duplicates=duplicates
    )
    event_repo.record_pipeline_run()

    stats = {
        "raw_signals": len(raw_signals),
        "filtered": len(filtered),
        "rejected": rejected,
        "events_created": created,
        "duplicates": duplicates,
        "total_stored": event_repo.count(),
    }

    logger.info("pipeline_cycle_complete", **stats)
    return stats


async def start_pipeline_loop(interval_seconds: int = 60):
    """Run the pipeline continuously.  First cycle runs immediately."""
    collectors = build_collectors()
    logger.info(
        "pipeline_started",
        collectors=[c.name for c in collectors],
        interval=interval_seconds,
    )

    cycle = 0
    while True:
        cycle += 1
        logger.info("pipeline_cycle_start", cycle=cycle)
        try:
            await run_pipeline_cycle(collectors)
        except Exception as e:
            logger.error("pipeline_cycle_error", cycle=cycle, error=str(e))

        await asyncio.sleep(interval_seconds)


if __name__ == "__main__":
    asyncio.run(start_pipeline_loop(interval_seconds=30))
