"""Kafka consumer for real-time graph updates."""

import asyncio
import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiokafka import AIOKafkaConsumer
from neo4j import AsyncGraphDatabase
from app.core.config import get_settings
from app.models.node import NodeCreate, NodeType
from app.models.edge import RelationshipType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def process_message(msg, driver):
    action = msg.get("action")
    if not action:
        return
    async with driver.session() as session:
        if action == "ADD_NODE":
            node = NodeCreate(id=msg["id"], type=NodeType(msg["type"]), name=msg["name"], metadata=msg.get("metadata", {}))
            await session.run(
                "MERGE (n:" + node.type.value + " {id: $id}) ON CREATE SET n.type=$type, n.name=$name ON MATCH SET n.name=$name",
                id=node.id, type=node.type.value, name=node.name,
            )
        elif action == "ADD_EDGE":
            from_id, to_id = msg["from"], msg["to"]
            rel_type = msg.get("type", "SERVES")
            weight = float(msg.get("weight", 0.8))
            conf = float(msg.get("confidence", 0.9))
            rel_enum = RelationshipType(rel_type)
            await session.run(
                "MATCH (a {id: $from_id}), (b {id: $to_id}) MERGE (a)-[r:" + rel_enum.value + "]->(b) SET r.weight=$w, r.confidence=$c",
                from_id=from_id, to_id=to_id, w=weight, c=conf,
            )
        elif action == "DELETE_NODE" and msg.get("id"):
            await session.run("MATCH (n {id: $id}) DETACH DELETE n", id=msg["id"])


async def consume():
    s = get_settings()
    driver = AsyncGraphDatabase.driver(s.neo4j_uri, auth=(s.neo4j_user, s.neo4j_password))
    consumer = AIOKafkaConsumer(
        s.kafka_graph_updates_topic, s.kafka_events_topic,
        bootstrap_servers=s.kafka_bootstrap_servers.split(","),
        group_id="graph-consumer",
        value_deserializer=lambda m: json.loads(m.decode()) if m else None,
    )
    await consumer.start()
    try:
        async for m in consumer:
            if m.value:
                try:
                    await process_message(m.value, driver)
                except Exception as e:
                    logger.exception("%s", e)
    finally:
        await consumer.stop()
        await driver.close()


if __name__ == "__main__":
    asyncio.run(consume())
