from functools import wraps
from inspect import signature

from fastapi import HTTPException, Request, status

from src.middleware.rate_limit.limiter import (
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