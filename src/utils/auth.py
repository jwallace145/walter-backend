from typing import Tuple

import bcrypt


def hash_password(password: str) -> Tuple[bytes, bytes]:
    """
    Hash the given password.

    This method just uses bcrypt: https://github.com/pyca/bcrypt

    Args:
        password: The password in plaintext before salting and hashing.s

    Returns:
        salt, password_hash
    """
    if isinstance(password, str) is False:
        raise TypeError("Password must be a string!")
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode(), salt)
    return salt, password_hash


def check_password(password: str, password_hash: str) -> bool:
    """
    Checks if a given password matches the given password hash.

    Args:
        password: The password in plaintext to check.
        password_hash: The hashed password to check against.

    Returns:
        boolean: True if the given password matches the given password hash, False otherwise.
    """
    if isinstance(password, str) is False or isinstance(password_hash, str) is False:
        raise TypeError("Password and password hash must both be strings!")
    return bcrypt.checkpw(password.encode(), password_hash.encode())
