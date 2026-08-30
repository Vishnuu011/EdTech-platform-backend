from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(
    BaseHTTPMiddleware
):

    """
    Middleware that adds security-related HTTP response headers.

    These headers provide browser-level protections against common
    web security risks such as MIME-type sniffing, clickjacking,
    unwanted referrer information, and unnecessary browser
    permissions.

    Headers added by this middleware:

    - ``X-Content-Type-Options``: Prevents MIME-type sniffing.
    - ``X-Frame-Options``: Prevents the application from being
      embedded in frames or iframes.
    - ``Referrer-Policy``: Controls how much referrer information
      is sent with outgoing requests.
    - ``Permissions-Policy``: Disables access to selected browser
      capabilities such as camera, microphone, and geolocation.
    """

    async def dispatch(
        self,
        request: Request,
        call_next,
    ):

        """
        Process the request and add security headers to the response.

        Args:
            request: Incoming HTTP request.
            call_next: Callable that forwards the request to the
                next middleware or endpoint.

        Returns:
            Response: HTTP response containing the configured
            security headers.
        """

        
        response = await call_next(request)

        response.headers[
            "X-Content-Type-Options"
        ] = "nosniff"

        response.headers[
            "X-Frame-Options"
        ] = "DENY"

        response.headers[
            "Referrer-Policy"
        ] = "strict-origin-when-cross-origin"

        response.headers[
            "Permissions-Policy"
        ] = (
            "camera=(), "
            "microphone=(), "
            "geolocation=()"
        )

        return response