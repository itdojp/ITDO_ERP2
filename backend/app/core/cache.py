from redis import Redis

from app.core.config import settings

redis_client = Redis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True
)


def get_cache(key: str) -> dict:
    return redis_client.get(key)


def set_cache(key: str, value: str, expire: int = 3600) -> dict:
    redis_client.setex(key, expire, value)


def delete_cache(key: str) -> dict:
    redis_client.delete(key)
