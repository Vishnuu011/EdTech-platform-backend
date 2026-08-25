from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.infrastructure.messaging.rabbitmq import rabbitmq
from src.infrastructure.messaging.consumer import start_consumer
from src.config.settings import settings




@asynccontextmanager
async def lifespan(app: FastAPI):

    await rabbitmq.connect()

    await start_consumer()

    yield

    await rabbitmq.close()


app=FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)    



if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )
