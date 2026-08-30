import aio_pika

from aio_pika import Connection, Channel, Message, DeliveryMode

from src.config.settings import settings
import json


class RabbitMQClient:

    """
    Asynchronous RabbitMQ client used for application messaging.

    Manages the RabbitMQ connection and channel lifecycle and provides
    a reusable method for publishing persistent JSON messages.

    The client uses ``aio_pika.connect_robust`` so the connection can
    automatically recover from temporary RabbitMQ connection failures.

    Attributes:
        connection: Active RabbitMQ connection, or ``None`` when
            disconnected.
        channel: Active RabbitMQ channel, or ``None`` when the client
            is disconnected.
    """


    def __init__(self):
        self.connection: Connection | None = None
        self.channel: Channel | None = None

    async def connect(self) -> None:

        """
        Establish a robust connection and channel to RabbitMQ.

        Creates a RabbitMQ connection using the configured connection
        URL and initializes a channel with a prefetch count of 10.

        The prefetch setting limits the number of unacknowledged
        messages that a consumer can receive at one time.

        Returns:
            None.
        """

        self.connection=await aio_pika.connect_robust(
            settings.RABBITMQ_URL
        )    


        self.channel=await self.connection.channel()

        await self.channel.set_qos(
            prefetch_count=10
        )

    async def close(self) -> None:

        """
        Close the RabbitMQ connection.

        Safely closes the active RabbitMQ connection when one exists
        and is not already closed.

        Returns:
            None.
        """

        if self.connection and not self.connection.is_closed:
            await self.connection.close()

    async def publish(
        self,
        exchange_name:str,
        routing_key:str,
        message:dict
    ) -> None:

        """
        Publish a persistent JSON message to a RabbitMQ topic exchange.

        The exchange is declared as durable and the published message
        is marked as persistent so RabbitMQ can retain it across broker
        restarts when the queue is also configured appropriately.

        Args:
            exchange_name: Name of the RabbitMQ exchange.
            routing_key: Topic routing key used to route the message
                to matching queues.
            message: Message payload represented as a Python dictionary.

        Returns:
            None.

        Raises:
            RuntimeError: If the RabbitMQ client is not connected.
            aio_pika.exceptions.AMQPError: If RabbitMQ rejects the
                operation or a messaging error occurs.
        """

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