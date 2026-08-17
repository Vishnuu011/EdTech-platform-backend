from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

CORRELATION_ID_HEADER= "X-Correlation-ID"


class CorrelationIDMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self, 
        request, 
        call_next    
    ) -> Response:

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