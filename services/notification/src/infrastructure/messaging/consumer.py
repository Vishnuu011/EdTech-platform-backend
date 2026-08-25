import json

from aio_pika import IncomingMessage

from src.infrastructure.messaging.rabbitmq import rabbitmq
from src.services.email import send_verification_email_to_send_grid


async def handle_email_verification(
    message: IncomingMessage
) -> None:

    async with message.process():

        event=json.loads(
            message.body.decode("utf-8")
        )

        print(
            "Received email verification event",
            event
        )
        data=event["data"]
        await send_verification_email_to_send_grid(
            destination=data["destination"],
            otp=data["otp"]
        )

async def start_consumer() -> None:

    await rabbitmq.consume(
        handle_email_verification
    )        