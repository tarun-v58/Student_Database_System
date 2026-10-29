from functools import lru_cache

from redis import Redis
from rq import Queue

from app.config import get_settings


@lru_cache
def get_redis() -> Redis:
    return Redis.from_url(
        get_settings().redis_url,
        socket_connect_timeout=2,
        socket_timeout=3,
    )


def get_report_queue() -> Queue:
    return Queue("reports", connection=get_redis())