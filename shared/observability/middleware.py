import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from shared.logging.logger import get_logger


logger=get_logger("http")


class ObservabilityMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:

        start_time=time.perf_counter()

        correlation_id=getattr(
            request.state,
            "correlation_id",
            None,
        )

        status_code=500

        try:
            resposne=await call_next(request)

            status_code=resposne.status_code

            return resposne
        finally:
            latency_ms=(
                time.perf_counter()-start_time
            )*1000

            logger.info(
                "HTTP request completed",
                extra={
                    "correlation_id": correlation_id,
                    "method":request.method,
                    "path":request.url.path,
                    "status_code":status_code,
                    "latency_ms":round(
                        latency_ms, 2
                    )
                }
            )