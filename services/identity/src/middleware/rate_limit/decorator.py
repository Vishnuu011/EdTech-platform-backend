from functools import wraps
from inspect import signature

from fastapi import HTTPException, Request, status

from src.middleware.rate_limit.service import (
    consume_rate_limit,
)


def _get_nested_value(
    obj,
    path: str,
):
    """
    Resolve nested values such as:

        data.email
        data.phone

    """
    value = obj

    for part in path.split("."):

        if isinstance(value, dict):
            value = value.get(part)

        else:
            value = getattr(
                value,
                part,
                None,
            )

        if value is None:
            return None

    return value


def rate_limit(
    limit: int,
    window_seconds: int,
    key_prefix: str,
    key_fields: list[str] | None = None,
):

    """
    Apply a Redis-backed rate limit to an asynchronous endpoint.

    The decorator creates a rate-limit key using the configured
    prefix, client IP address, and optionally one or more fields
    from the endpoint arguments.

    Rate-limit state is stored in Redis and consumed through an
    atomic Redis operation. When the request limit is exceeded,
    the endpoint returns HTTP 429 with a ``Retry-After`` header
    indicating when the current rate-limit window is expected
    to expire.

    Args:
        limit: Maximum number of requests allowed during the
            configured time window.
        window_seconds: Duration of the rate-limit window in seconds.
        key_prefix: Prefix used to namespace the Redis rate-limit key.
            Example: ``"login"``.
        key_fields: Optional list of argument paths used to create
            a more specific rate-limit key.

            Examples:
                ``["data.email"]``
                ``["data.email", "data.phone"]``

            Nested fields are resolved from the endpoint's bound
            arguments.

    Returns:
        Callable: A decorator that applies rate limiting to an
        asynchronous endpoint.

    Raises:
        RuntimeError: If the decorated endpoint does not contain
            a ``Request`` parameter or a configured key field cannot
            be found.

    Raises:
        HTTPException: 429 Too Many Requests when the configured
            request limit has been exceeded.

    Example:
        @rate_limit(
            limit=5,
            window_seconds=300,
            key_prefix="login-verify",
            key_fields=["data.email"],
        )
        async def verify_login(
            request: Request,
            data: LoginVerifyRequest,
        ):
            ...
    """

    
    def decorator(func):

        sig = signature(func)

        @wraps(func)
        async def wrapper(
            *args,
            **kwargs,
        ):

            bound = sig.bind_partial(
                *args,
                **kwargs,
            )

            request: Request | None = (
                bound.arguments.get("request")
            )

            if request is None:
                raise RuntimeError(
                    "Rate-limited endpoint must have "
                    "a Request parameter"
                )

            client_ip = (
                request.client.host
                if request.client
                else "unknown"
            )

            key_parts = [
                key_prefix,
                f"ip:{client_ip}",
            ]

            if key_fields:

                for field_path in key_fields:

                    value = _get_nested_value(
                        bound.arguments,
                        field_path,
                    )

                    if value is None:
                        raise RuntimeError(
                            f"Rate limit field "
                            f"'{field_path}' not found"
                        )

                    value = str(
                        value
                    ).lower().strip()

                    key_parts.append(
                        f"{field_path.replace('.', '_')}:{value}"
                    )

            key = ":".join(key_parts)

            allowed, ttl = await consume_rate_limit(
                key=key,
                limit=limit,
                window_seconds=window_seconds,
            )

            if not allowed:

                raise HTTPException(
                    status_code=(
                        status.HTTP_429_TOO_MANY_REQUESTS
                    ),
                    detail=(
                        "Too many requests. "
                        "Please try again later."
                    ),
                    headers={
                        "Retry-After": str(
                            max(ttl, 1)
                        )
                    },
                )

            return await func(
                *args,
                **kwargs,
            )

        return wrapper

    return decorator