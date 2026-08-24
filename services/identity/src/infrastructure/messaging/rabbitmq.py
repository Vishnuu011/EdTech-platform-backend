import aio_pika

from aio_pika import Connection, Channel, Message, DeliveryMode

from src.config.settings import settings
import json


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

    async def publish(
        self,
        exchange_name:str,
        routing_key:str,
        message:dict
    ) -> None:

        if self.channel is None:

            raise RuntimeError(
                "RabbitMQ is not connected"
            )        

        exchange=await self.channel.declare_exchange(
            exchange_name,
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )

        body=json.dumps(message).encode()

        await exchange.publish(
            Message(
                body=body,
                content_type="application/json",
                delivery_mode=DeliveryMode.PERSISTENT
            ),
            routing_key=routing_key
        )


rabbitmq = RabbitMQClient()                