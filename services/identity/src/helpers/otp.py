import hashlib
import secrets

OTP_LENGTH=6
OTP_RESEND_COOLDOWN_SECOND=60
OTP_EXPIRE_SECONDS=300


def generate_otp()-> str:

    """
    Generate a cryptographically secure numeric one-time password.

    Generates a six-digit OTP using Python's cryptographically secure
    random number generator. Leading zeros are preserved.

    Returns:
        str: A zero-padded six-digit OTP.
    """

    return f"{secrets.randbelow(1_000_000):06d}"




def hash_otp(otp: str) -> str:

    """
    Hash an OTP using SHA-256.

    The plaintext OTP is never required to be stored. Instead, its
    SHA-256 hash can be stored temporarily and used later to verify
    the submitted OTP.

    Args:
        otp: Plaintext OTP to hash.

    Returns:
        str: Hexadecimal SHA-256 hash of the OTP.
    """

    return hashlib.sha256(
        otp.encode("utf-8")
    ).hexdigest()




def verify_otp(otp: str, hashed_otp: str) -> bool:

    """
    Verify an OTP against a previously generated hash.

    Uses a constant-time comparison to reduce the risk of
    timing-based attacks during hash comparison.

    Args:
        otp: Plaintext OTP supplied by the user.
        hashed_otp: Previously stored SHA-256 OTP hash.

    Returns:
        bool: ``True`` if the OTP matches the hash; otherwise ``False``.
    """

    return hash_otp(otp=otp)==hashed_otp