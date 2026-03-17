import json
from typing import Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError
from utils.config_loader import get_settings
from utils.logger import logger

settings = get_settings()

TOPICS = {
    "raw_signals": "swift.raw_signals",
    "filtered_signals": "swift.filtered_signals",
    "detected_events": "swift.detected_events",
    "structured_events": "swift.structured_events",
}

_producer: Optional[KafkaProducer] = None


def _kafka_security_kwargs() -> dict:
    """Build Kafka security kwargs from config."""
    proto = settings.kafka_security_protocol
    if proto == "PLAINTEXT":
        return {}
    kwargs: dict = {"security_protocol": proto}
    if proto in ("SSL", "SASL_SSL"):
        kwargs["ssl_check_hostname"] = True
        if settings.kafka_ssl_cafile:
            kwargs["ssl_cafile"] = settings.kafka_ssl_cafile
        elif settings.tls_ca_file:
            kwargs["ssl_cafile"] = settings.tls_ca_file
    return kwargs


def get_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        try:
            _producer = KafkaProducer(
                bootstrap_servers=settings.kafka_broker,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks="all",
                retries=3,
                max_in_flight_requests_per_connection=1,
                **_kafka_security_kwargs(),
            )
            logger.info("kafka_producer_connected", broker=settings.kafka_broker,
                        security=settings.kafka_security_protocol)
        except KafkaError as e:
            logger.error("kafka_producer_failed", error=str(e))
            raise
    return _producer


def publish(topic_key: str, message: dict, key: Optional[str] = None) -> None:
    topic = TOPICS.get(topic_key, topic_key)
    try:
        producer = get_producer()
        future = producer.send(topic, value=message, key=key)
        future.get(timeout=10)
        logger.debug("message_published", topic=topic, key=key)
    except KafkaError as e:
        logger.error("publish_failed", topic=topic, error=str(e))
        raise


def publish_raw_signal(signal: dict) -> None:
    publish("raw_signals", signal, key=signal.get("signal_id"))


def publish_filtered_signal(signal: dict) -> None:
    publish("filtered_signals", signal, key=signal.get("signal_id"))


def publish_detected_event(event: dict) -> None:
    publish("detected_events", event, key=event.get("event_id"))


def publish_structured_event(event: dict) -> None:
    publish("structured_events", event, key=event.get("event_id"))
