import json
from functools import wraps
from typing import Callable

import redis

from api.config import get_settings


def get_redis():
    settings = get_settings()
    try:
        return redis.from_url(settings.redis_url, decode_responses=True)
    except redis.RedisError:
        return None


def cached(key_prefix: str):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            client = get_redis()
            if not client:
                return func(*args, **kwargs)
            key = f"{key_prefix}:{hash((args, tuple(sorted(kwargs.items()))))}"
            hit = client.get(key)
            if hit:
                return json.loads(hit)
            result = func(*args, **kwargs)
            client.setex(key, get_settings().cache_ttl_seconds, json.dumps(result, default=str))
            return result

        return wrapper

    return decorator
