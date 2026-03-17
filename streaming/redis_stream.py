"""Redis Streams fallback for environments without Kafka.

Supports TLS (rediss://) and password auth via settings.
"""

import json
import ssl
from typing import Callable, Optional
import redis
from utils.config_loader import get_settings
from utils.logger import logger

settings = get_settings()

_redis_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        url = settings.redis_url
        kwargs: dict = {"decode_responses": True}

        if settings.redis_ssl:
            if not url.startswith("rediss://"):
                url = url.replace("redis://", "rediss://", 1)
            ssl_ctx = ssl.create_default_context()
            if settings.tls_ca_file:
                ssl_ctx.load_verify_locations(settings.tls_ca_file)
            kwargs["ssl"] = True
            kwargs["ssl_ca_certs"] = settings.tls_ca_file or None

        if settings.redis_password:
            kwargs["password"] = settings.redis_password

        _redis_client = redis.from_url(url, **kwargs)
        logger.info("redis_connected", url=url.split("@")[-1],
                     ssl=settings.redis_ssl)
    return _redis_client


def publish_to_stream(stream_name: str, data: dict) -> str:
    r = get_redis()
    message_id = r.xadd(stream_name, {"payload": json.dumps(data, default=str)})
    logger.debug("redis_stream_published", stream=stream_name, message_id=message_id)
    return message_id


def consume_stream(
    stream_name: str,
    group_name: str,
    consumer_name: str,
    handler: Callable[[dict], None],
    batch_size: int = 10,
    block_ms: int = 5000,
) -> None:
    r = get_redis()

    try:
        r.xgroup_create(stream_name, group_name, id="0", mkstream=True)
    except redis.exceptions.ResponseError:
        pass

    logger.info("redis_consume_started", stream=stream_name, group=group_name)

    while True:
        try:
            messages = r.xreadgroup(
                group_name, consumer_name, {stream_name: ">"}, count=batch_size, block=block_ms
            )
            if not messages:
                continue

            for _, entries in messages:
                for msg_id, fields in entries:
                    try:
                        data = json.loads(fields["payload"])
                        handler(data)
                        r.xack(stream_name, group_name, msg_id)
                    except Exception as e:
                        logger.error("redis_message_failed", msg_id=msg_id, error=str(e))

        except KeyboardInterrupt:
            logger.info("redis_consume_stopped", stream=stream_name)
            break
