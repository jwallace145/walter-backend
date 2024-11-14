from dataclasses import dataclass
import datetime as dt
from typing import Tuple

import bcrypt
import jwt

from src.config import CONFIG
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class WalterAuthenticator:
    """
    Authenticator
    """

    jwt_secret_key: str

    def generate_token(self, email: str) -> str:
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
        now = dt.datetime.now(dt.UTC)
        return jwt.encode(
            {
                "sub": email,
                "iat": now,
                "exp": now + dt.timedelta(days=7),
            },
            self.jwt_secret_key,
            algorithm=CONFIG.jwt_algorithm,
        )

    def decode_token(self, token: str) -> bool | None:
        """
        Decode the given JSON web token to verify user identity.

        Args:
            token: The JSON web token given to a user after successful authentication.
            key: The JWT secret key used to decode the token (stored in SecretsManager).

        Returns:
            True if the token is valid, False otherwise.
        """
        try:
            return jwt.decode(
                token, self.jwt_secret_key, algorithms=[CONFIG.jwt_algorithm]
            )
        except jwt.ExpiredSignatureError:
            print("Token has expired")
            return None
        except jwt.InvalidTokenError:
            print("Invalid token")
            return None

    def hash_password(self, password: str) -> Tuple[bytes, bytes]:
        """
        Hash the given password.

        This method just uses bcrypt: https://github.com/pyca/bcrypt

        Args:
            password: The password in plaintext before salting and hashing.

        Returns:
            salt, password_hash
        """
        if isinstance(password, str) is False:
            raise TypeError("Password must be a string!")
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode(), salt)
        return salt, password_hash

    def check_password(self, password: str, password_hash: str) -> bool:
        """
        Checks if a given password matches the given password hash.

        Args:
            password: The password in plaintext to check.
            password_hash: The hashed password to check against.

        Returns:
            boolean: True if the given password matches the given password hash, False otherwise.
        """
        if (
            isinstance(password, str) is False
            or isinstance(password_hash, str) is False
        ):
            raise TypeError("Password and password hash must both be strings!")
        return bcrypt.checkpw(password.encode(), password_hash.encode())

    def get_token(self, event: dict) -> str | None:
        if event["headers"] is None or "Authorization" not in event["headers"]:
            return None
        return event["headers"]["Authorization"].split(" ")[1]
