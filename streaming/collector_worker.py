"""Worker that runs all collectors on a schedule and pushes raw signals to Kafka."""

import asyncio
import time
from utils.logger import logger
from collectors.news_api_collector import NewsAPICollector
from collectors.rss_collector import RSSCollector
from collectors.weather_api_collector import WeatherAPICollector
from streaming.producer import publish_raw_signal

COLLECTION_INTERVAL_SECONDS = 60


async def run_collectors():
    collectors = [
        NewsAPICollector(),
        RSSCollector(),
        WeatherAPICollector(),
    ]

    while True:
        for collector in collectors:
            try:
                logger.info("collector_run_start", collector=collector.name)
                signals = await collector.collect()
                for signal in signals:
                    try:
                        publish_raw_signal(signal)
                    except Exception as e:
                        logger.warning("publish_skipped_kafka_unavailable", error=str(e))
                logger.info(
                    "collector_run_complete",
                    collector=collector.name,
                    signal_count=len(signals),
                )
            except Exception as e:
                logger.error("collector_run_failed", collector=collector.name, error=str(e))

        await asyncio.sleep(COLLECTION_INTERVAL_SECONDS)


if __name__ == "__main__":
    logger.info("collector_worker_starting")
    asyncio.run(run_collectors())
