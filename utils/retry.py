"""Exponential backoff + retry utilities for collectors and external APIs."""

import asyncio
import random
from functools import wraps
from typing import Callable, TypeVar, Tuple, Type

from utils.logger import logger

T = TypeVar("T")

DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0
DEFAULT_MAX_DELAY = 60.0
DEFAULT_JITTER = 0.1


def _compute_delay(attempt: int, base_delay: float, max_delay: float, jitter: float) -> float:
    """Exponential backoff: base * 2^attempt, capped, with jitter."""
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter_amount = delay * jitter * (2 * random.random() - 1)
    return max(0.01, delay + jitter_amount)


async def retry_async(
    fn: Callable[[], T],
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    jitter: float = DEFAULT_JITTER,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    context: str = "",
) -> T:
    """Execute async callable with exponential backoff. Raises last exception if all retries fail."""
    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            result = await fn()
            if attempt > 0:
                logger.info("retry_succeeded", context=context, attempt=attempt)
            return result
        except retryable_exceptions as e:
            last_exc = e
            if attempt == max_retries:
                logger.error("retry_exhausted", context=context, attempts=max_retries + 1, error=str(e))
                raise
            delay = _compute_delay(attempt, base_delay, max_delay, jitter)
            logger.warning("retry_scheduled", context=context, attempt=attempt + 1, delay=round(delay, 2), error=str(e))
            await asyncio.sleep(delay)
    raise last_exc
