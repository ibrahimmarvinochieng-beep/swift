import json
from typing import Callable, Optional
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from utils.config_loader import get_settings
from utils.logger import logger

settings = get_settings()


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


def create_consumer(
    topic: str,
    group_id: str,
    auto_offset_reset: str = "latest",
) -> KafkaConsumer:
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=settings.kafka_broker,
            group_id=group_id,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=False,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            max_poll_records=50,
            session_timeout_ms=30000,
            **_kafka_security_kwargs(),
        )
        logger.info("kafka_consumer_connected", topic=topic, group_id=group_id,
                     security=settings.kafka_security_protocol)
        return consumer
    except KafkaError as e:
        logger.error("kafka_consumer_failed", topic=topic, error=str(e))
        raise


def consume_loop(
    topic: str,
    group_id: str,
    handler: Callable[[dict], None],
    error_handler: Optional[Callable[[Exception, dict], None]] = None,
) -> None:
    consumer = create_consumer(topic, group_id)
    logger.info("consume_loop_started", topic=topic)

    try:
        for message in consumer:
            try:
                handler(message.value)
                consumer.commit()
            except Exception as e:
                logger.error(
                    "message_processing_failed",
                    topic=topic,
                    offset=message.offset,
                    error=str(e),
                )
                if error_handler:
                    error_handler(e, message.value)
    except KeyboardInterrupt:
        logger.info("consume_loop_stopped", topic=topic)
    finally:
        consumer.close()
