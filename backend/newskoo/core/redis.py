"""Redis helpers: shared client, per-domain token-bucket rate limiting, and a
seen-set used for cheap URL/hash dedup gating."""

from __future__ import annotations

import time

import redis.asyncio as aioredis

from newskoo.core.config import get_settings

_client: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _client
    if _client is None:
        _client = aioredis.from_url(
            get_settings().redis_url, encoding="utf-8", decode_responses=True
        )
    return _client


# Token-bucket as a Lua script (atomic). Returns 1 if allowed, 0 if throttled.
_TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local rate = tonumber(ARGV[1])      -- tokens per second
local capacity = tonumber(ARGV[2])  -- bucket size
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])
local data = redis.call('HMGET', key, 'tokens', 'ts')
local tokens = tonumber(data[1])
local ts = tonumber(data[2])
if tokens == nil then tokens = capacity; ts = now end
local delta = math.max(0, now - ts)
tokens = math.min(capacity, tokens + delta * rate)
local allowed = 0
if tokens >= requested then
  tokens = tokens - requested
  allowed = 1
end
redis.call('HMSET', key, 'tokens', tokens, 'ts', now)
redis.call('EXPIRE', key, math.ceil(capacity / rate) + 1)
return allowed
"""


class RateLimiter:
    """Per-domain polite rate limiting backed by Redis token buckets."""

    def __init__(self, redis: aioredis.Redis | None = None) -> None:
        self._redis = redis or get_redis()
        self._script = self._redis.register_script(_TOKEN_BUCKET_LUA)

    async def allow(self, domain: str, rate: float, capacity: float = 1.0) -> bool:
        now = time.time()
        res = await self._script(
            keys=[f"rl:{domain}"], args=[rate, capacity, now, 1]
        )
        return bool(res)


class SeenSet:
    """Bloom-ish seen tracking. Uses a Redis SET (swap for RedisBloom in prod)."""

    def __init__(self, name: str, redis: aioredis.Redis | None = None) -> None:
        self._redis = redis or get_redis()
        self._key = f"seen:{name}"

    async def add_if_absent(self, member: str) -> bool:
        """Return True if newly added (i.e. *not* seen before)."""
        return bool(await self._redis.sadd(self._key, member))

    async def contains(self, member: str) -> bool:
        return bool(await self._redis.sismember(self._key, member))
