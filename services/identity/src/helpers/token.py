import hashlib
import hmac



def hash_token(token: str) -> str:

    """
    Hash a high-entropy token using SHA-256.

    Intended for tokens such as refresh tokens that are generated
    using a cryptographically secure random source. The plaintext
    token should not be stored in the database.

    Args:
        token: Plaintext token to hash.

    Returns:
        str: Hexadecimal SHA-256 hash of the token.
    """

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()




def verify_token_hash(
    token: str,
    token_hash: str,
) -> bool:
    """
    Verify a token against its stored SHA-256 hash.

    Uses a constant-time comparison to reduce timing-attack
    information leakage.

    Args:
        token: Plaintext token supplied by the client.
        token_hash: Previously stored SHA-256 token hash.

    Returns:
        bool: ``True`` if the token matches the stored hash;
        otherwise ``False``.
    """

    calculated_hash = hash_token(
        token=token
    )

    return hmac.compare_digest(
        calculated_hash,
        token_hash,
    )