from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


_password_hasher=PasswordHasher()


def hash_password(password: str) -> str:

    """
    Securely hash a user's password using Argon2.

    Argon2 is a memory-hard password hashing algorithm designed to
    make brute-force and password-cracking attacks more expensive.

    Args:
        password: Plaintext password to hash.

    Returns:
        str: Argon2 password hash containing the parameters and salt
        required for later verification.
    """

    return _password_hasher.hash(
        password=password
    )



def verify_password(password: str, password_hash: str) -> bool:

    """
    Verify a plaintext password against an Argon2 password hash.

    Args:
        password: Plaintext password supplied by the user.
        password_hash: Previously stored Argon2 password hash.

    Returns:
        bool: ``True`` when the password matches the stored hash;
        otherwise ``False``.
    """

    try:
        return _password_hasher.verify(
            hash=password_hash,
            password=password
        )
    except VerifyMismatchError:
        return False