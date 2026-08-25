import hashlib
import secrets

OTP_LENGTH=6
OTP_RESEND_COOLDOWN_SECOND=60
OTP_EXPIRE_SECONDS=300


def generate_otp()-> str:

    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(otp: str) -> str:

    return hashlib.sha256(
        otp.encode("utf-8")
    ).hexdigest()


def verify_otp(otp: str, hashed_otp: str) -> bool:

    return hash_otp(otp=otp)==hashed_otp