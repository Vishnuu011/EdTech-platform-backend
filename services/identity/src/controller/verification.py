from src.helpers.otp import (
    OTP_EXPIRE_SECONDS,
    OTP_LENGTH,
    hash_otp,
    verify_otp,
    generate_otp
)

from src.infrastructure.redis.client import redis_client
from src.infrastructure.messaging.events import publish_email_verification_event




def get_otp_key(
    verification_type:str,
    destination:str
) -> str:

    return (
        f"identity:otp:"
        f"{verification_type}:"
        f"{destination}"
    )




async def create_otp(
    user_id:str,
    verification_type: str,
    destination: str
) -> str:

    otp=generate_otp()

    otp_hash=hash_otp(
        otp=otp
    )

    key=get_otp_key(
        verification_type,
        destination
    )

    await redis_client.set(
        key,
        otp_hash,
        ex=OTP_EXPIRE_SECONDS
    )

    await publish_email_verification_event(
        user_id=user_id,
        destination=destination,
        otp=otp
    )

    return otp



async def check_otp(
    verification_type:str,
    destination:str,
    otp:str
) -> bool:

    key=get_otp_key(
        verification_type,
        destination
    )

    stored_hash=await redis_client.get(
        key
    )

    if stored_hash is None:
        return False

    if not verify_otp(
        otp,
        stored_hash
    ):

        return False

    await redis_client.delete(key)

    return True