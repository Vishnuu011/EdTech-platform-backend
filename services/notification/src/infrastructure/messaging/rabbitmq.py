import aio_pika
from aio_pika import Connection
from src.config.settings import settings

EXCHANGE_NAME="edtech.events"
QUEUE_NAME="notification.email"

EMAIL_VERIFICATION_ROUTING_KEY=(
    "identity.email_verification_requested"
)

class RabbitMQClient:

    def __init__(self):

        self.connection: Connection | None = None
        self.channel=None

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

    async def consume(self, callback) -> None:

        if self.channel is None:

            raise RuntimeError(
                "RabbitMQ is not connected"
            )   

        exchange=await self.channel.declare_exchange(
            EXCHANGE_NAME,
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )         

        queue=await self.channel.declare_queue(
            QUEUE_NAME,
            durable=True
        )

        await queue.bind(
            exchange,
            routing_key=EMAIL_VERIFICATION_ROUTING_KEY
        )

        await queue.consume(callback)


rabbitmq=RabbitMQClient()        