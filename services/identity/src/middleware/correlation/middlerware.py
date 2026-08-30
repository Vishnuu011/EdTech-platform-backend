from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from collections.abc import Callable
from starlette.requests import Request
from starlette.responses import Response

CORRELATION_ID_HEADER= "X-Correlation-ID"


class CorrelationIDMiddleware(BaseHTTPMiddleware):

    """
    Middleware that assigns a correlation ID to each HTTP request.

    If the incoming request contains a correlation ID header, the
    existing value is reused. Otherwise, a new UUID is generated.

    The correlation ID is stored in ``request.state`` so it can be
    accessed by downstream application code and is also returned
    in the response headers.
    """

    async def dispatch(
        self, 
        request:Request, 
        call_next:Callable    
    ) -> Response:

        """
        Process an HTTP request and attach its correlation ID.

        Args:
            request: Incoming FastAPI/Starlette HTTP request.
            call_next: Callable that passes the request to the next
                middleware or application endpoint.

        Returns:
            Response: HTTP response containing the correlation ID
            in the configured response header.
        """

        correlation_id=request.headers.get(
            CORRELATION_ID_HEADER
        )

        if not correlation_id:
            correlation_id=str(uuid4())

        request.state.correlation_id = correlation_id

        response=await call_next(request)
        response.headers[
            CORRELATION_ID_HEADER
        ]=correlation_id

        return response    