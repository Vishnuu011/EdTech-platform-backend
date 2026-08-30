import uuid
from datetime import datetime, timezone

from src.infrastructure.messaging.rabbitmq import rabbitmq


EXCHANGE_NAME="edtech.events"

async def publish_verification_event(
    user_id:str,
    destination:str,
    otp:str,
    verification_type:str
) -> None:

    """
    Publish an identity verification event to RabbitMQ.

    Creates an event containing a unique event ID, event type,
    occurrence timestamp, source service, and verification data.
    The event is published to the shared EdTech events exchange
    using the identity verification routing key.

    Args:
        user_id: Unique identifier of the user requesting verification.
        destination: Verification destination, such as the user's
            email address.
        otp: One-time verification code to be delivered to the user.
        verification_type: Type of verification being requested,
            such as email verification, login OTP, or password reset.

    Returns:
        None: The function publishes the event asynchronously and
        does not return a value.

    Raises:
        Exception: Propagates messaging-related exceptions when
            the event cannot be published to RabbitMQ.
    """


    event={
        "event_id":str(uuid.uuid4()),
        "event_type":"identity.verification_requested",
        "occurred_at":datetime.now(
            timezone.utc
        ).isoformat(),
        "source":"identity-service",
        "data": {
            "user_id":user_id,
            "destination":destination,
            "otp":otp,
            "verification_type":verification_type
        }
    }

    await rabbitmq.publish(
        exchange_name=EXCHANGE_NAME,
        routing_key="identity.verification_requested",
        message=event
    )