"""Create Kafka topics for graph updates."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings


async def create_topics():
    """Ensure graph.updates and events.graph_modifications topics exist."""
    settings = get_settings()
    brokers = settings.kafka_bootstrap_servers.split(",")
    topics = [settings.kafka_graph_updates_topic, settings.kafka_events_topic]
    try:
        from aiokafka.admin import AIOKafkaAdminClient, NewTopic
        admin = AIOKafkaAdminClient(bootstrap_servers=brokers)
        await admin.start()
        existing = await admin.list_topics()
        to_create = [NewTopic(t, num_partitions=3, replication_factor=1) for t in topics if t not in existing]
        if to_create:
            await admin.create_topics(to_create)
            print(f"Created topics: {[t.name for t in to_create]}")
        else:
            print(f"Topics already exist: {topics}")
        await admin.close()
    except ImportError:
        print("aiokafka admin not available; create topics manually:")
        for t in topics:
            print(f"  kafka-topics --create --topic {t} --bootstrap-server {brokers[0]}")
    except Exception as e:
        print(f"Error: {e}")
        print("Create topics manually:")
        for t in topics:
            print(f"  kafka-topics --create --topic {t} --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1")


if __name__ == "__main__":
    asyncio.run(create_topics())
