from src.config.settings import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time
from src.middleware.error import (
    register_exception_handlers
)

app=FastAPI(
    title=settings.APP_NAME,
    description="Identity Service for EdTech Platform",
    version=settings.APP_VERSION,
)

register_exception_handlers(
    app=app
)

@app.middleware("http")
async def add_process_time_header(
    request, call_next
):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

