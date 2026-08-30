from src.infrastructure.redis.client import redis_client


RATE_LIMIT_SCRIPT = """
local current = redis.call("INCR", KEYS[1])

if current == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
end

local ttl = redis.call("TTL", KEYS[1])

return {current, ttl}
"""


async def consume_rate_limit(
    key: str,
    limit: int,
    window_seconds: int,
) -> tuple[bool, int]:

    redis_key = f"identity:rate-limit:{key}"

    result = await redis_client.eval(
        RATE_LIMIT_SCRIPT,
        1,
        redis_key,
        window_seconds,
    )

    count = int(result[0])
    ttl = int(result[1])

    return count <= limit, ttl