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

    """
    Consume one request from a fixed-window Redis rate limiter.

    The request count is stored in Redis using an atomic Lua script.
    The counter is incremented and its expiration time is initialized
    when the first request enters the window.

    Args:
        key: Unique identifier for the rate-limit bucket, such as
            an IP address, email address, user ID, or endpoint key.
        limit: Maximum number of requests permitted within the window.
        window_seconds: Duration of the rate-limit window in seconds.

    Returns:
        tuple[bool, int]:
            A tuple containing:
            - bool: ``True`` if the request is within the configured
              limit, otherwise ``False``.
            - int: Number of seconds remaining before the current
              rate-limit window expires.

    Example:
        allowed, retry_after = await consume_rate_limit(
            key="login:user@example.com",
            limit=5,
            window_seconds=300,
        )

        if not allowed:
            # Request should be rejected.
            ...

    Notes:
        The Lua script ensures that the counter increment and initial
        expiration are performed atomically by Redis, preventing race
        conditions when multiple requests arrive concurrently.
    """

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