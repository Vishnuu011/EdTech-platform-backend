import uuid
from datetime import datetime, timezone

from src.infrastructure.messaging.rabbitmq import rabbitmq


EXCHANGE_NAME="edtech.events"

async def publish_email_verification_event(
    user_id:str,
    destination:str,
    otp:str
) -> None:


    event={
        "event_id":str(uuid.uuid4()),
        "event_type":"identity.email_verification_requested",
        "occurred_at":datetime.now(
            timezone.utc
        ).isoformat(),
        "source":"identity-service",
        "data": {
            "user_id":user_id,
            "destination":destination,
            "otp":otp
        }
    }

    await rabbitmq.publish(
        exchange_name=EXCHANGE_NAME,
        routing_key="identity.email_verification_requested",
        message=event
    )