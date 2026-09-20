from typing import Dict, Any
import redis
from app.core.config import settings
from app.core.logging import logger

_redis_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    """
    Provides a reusable Redis client instance connected to REDIS_URL.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_timeout=3.0,
            socket_connect_timeout=3.0,
        )
    return _redis_client


def check_redis_connection() -> Dict[str, Any]:
    """
    Verifies Redis server connectivity by issuing a PING command.
    Returns a status dictionary or raises an Exception.
    """
    client = get_redis_client()
    response = client.ping()
    if not response:
        raise ValueError("Redis ping returned False")
    return {
        "connected": True,
        "ping": "pong",
    }
