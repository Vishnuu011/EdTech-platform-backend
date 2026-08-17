import aio_pika

from aio_pika import Connection, Channel

from src.config.settings import settings


class RabbitMQClient:

    def __init__(self):
        self.connection: Connection | None = None
        self.channel: Channel | None = None

    async def connect(self) -> None:

        self.connection=await aio_pika.connect_robust(
            settings.RABBITMQ_URL
        )    


        self.channel=await self.connection.channel()

        await self.channel.set_qos(
            prefetch_count=10
        )

    async def close(self) -> None:
        if self.connection and not self.connection.is_closed:
            await self.connection.close()


rabbitmq = RabbitMQClient()                