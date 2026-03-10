import os
import redis

def get_redis():
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", 6379))
    return redis.Redis(host=host, port=port, decode_responses=True)

def incr_with_ttl(r, key: str, ttl_seconds: int = 3600):
    value = r.incr(key)
    r.expire(key, ttl_seconds)
    return value
