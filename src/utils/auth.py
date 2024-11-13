from datetime import datetime, timedelta
from typing import Tuple

import bcrypt
import jwt

from src.config import CONFIG


def generate_token(email: str, key: str) -> str:
    """
    Generate JSON web token for user email.

    After a user successfully authenticates themselves via login, Walter creates
    a token to give to the user to verify their identity. This allows the user
    to make subsequent authenticated requests. The token is generated via JSON
    web tokens with the algorithm specified in Walter's configs.

    Args:
        email: The user email to generate the JSON web token.
        key:  The JWT secret key used to encode the user email and token information.

    Returns:
        The JSON web token for the authenticated user.
    """
    return jwt.encode(
        {
            "sub": email,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1),
        },
        key,
        algorithm=CONFIG.jwt_algorithm,
    )


def decode_token(token: str, key: str) -> bool | None:
    """
    Decode the given JSON web token to verify user identity.

    Args:
        token: The JSON web token given to a user after successful authentication.
        key: The JWT secret key used to decode the token (stored in SecretsManager).

    Returns:
        True if the token is valid, False otherwise.
    """
    try:
        return jwt.decode(token, key, algorithms=[CONFIG.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        print("Token has expired")
        return None
    except jwt.InvalidTokenError:
        print("Invalid token")
        return None


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
