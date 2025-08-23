import secrets
import string
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import bcrypt
import jwt

from src.auth.models import Tokens, TokenType
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class WalterAuthenticator:
    """
    Walter Authenticator
    """

    walter_sm: WalterSecretsManagerClient

    ACCESS_TOKEN_EXPIRY_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRY_DAYS: int = 7

    def generate_tokens(self, user_id: str) -> Tokens:
        """
        Generate access and refresh tokens for a user.

        This method creates a pair of JWT tokens for authentication:
        - Access token: Short-lived token (15 min) used for API authentication
        - Refresh token: Long-lived token (7 days) used to obtain new access tokens

        Both tokens share the same JTI (JWT ID) for tracking purposes.

        Args:
            user_id: The unique identifier of the user to generate tokens for

        Returns:
            Tokens: Object containing the generated access_token and refresh_token
        """
        # generate token expiry times
        now = datetime.now(timezone.utc)
        access_token_expiry = now + timedelta(minutes=self.ACCESS_TOKEN_EXPIRY_MINUTES)
        refresh_token_expiry = now + timedelta(days=self.REFRESH_TOKEN_EXPIRY_DAYS)

        # generate unique token id for tracking the access and refresh tokens
        jti = WalterAuthenticator._generate_jti()

        # access token payload, contains user data for api calls
        access_payload = {
            "sub": user_id,
            "iat": int(now.timestamp()),
            "exp": int(access_token_expiry.timestamp()),
            "type": TokenType.ACCESS.value,
            "jti": jti,  # same id as refresh token
        }

        # refresh token payload, contains user data for getting new access tokens
        refresh_payload = {
            "sub": user_id,
            "iat": int(now.timestamp()),
            "exp": int(refresh_token_expiry.timestamp()),
            "type": TokenType.REFRESH.value,
            "jti": jti,  # same id as access token
        }

        access_token = jwt.encode(
            access_payload,
            self.walter_sm.get_access_token_secret_key(),
            algorithm="HS256",
        )

        refresh_token = jwt.encode(
            refresh_payload,
            self.walter_sm.get_refresh_token_secret_key(),
            algorithm="HS256",
        )

        return Tokens(
            jti, access_token, refresh_token, access_token_expiry, refresh_token_expiry
        )

    def decode_access_token(self, access_token: str) -> Optional[Tuple[str, str]]:
        try:
            payload = jwt.decode(
                access_token,
                self.walter_sm.get_access_token_secret_key(),
                algorithms=["HS256"],
            )

            token_type = payload.get("type")
            if token_type != TokenType.ACCESS.value:
                log.error(f"Invalid token type: {token_type}")
                return None

            user_id = payload["sub"]
            jti = payload["jti"]

            return user_id, jti

        except jwt.ExpiredSignatureError:
            log.error("Access token has expired!")
            return None
        except jwt.InvalidTokenError as e:
            log.error(f"Invalid access token: {e}")
            return None

    def decode_refresh_token(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        try:
            payload = jwt.decode(
                refresh_token,
                self.walter_sm.get_refresh_token_secret_key(),
                algorithms=["HS256"],
            )

            token_type = payload.get("type")
            if token_type != TokenType.REFRESH.value:
                log.error(f"Invalid token type for refresh: {token_type}")
                return None

            user_id = payload["sub"]
            jti = payload["jti"]

            return user_id, jti

        except jwt.ExpiredSignatureError:
            log.error("Refresh token has expired!")
            return None
        except jwt.InvalidTokenError as e:
            log.error(f"Invalid refresh token: {e}")
            return None

    def generate_access_token(self, user_id: str, jti: str) -> Tuple[str, datetime]:
        """
        Generate a new access token for the given user with the provided JTI.
        Returns (access_token, access_token_expiry).
        """
        # generate access token expiry time
        now = datetime.now(timezone.utc)
        access_token_expiry = now + timedelta(minutes=self.ACCESS_TOKEN_EXPIRY_MINUTES)

        # create new access token payload with existing user_id and jti of the parent refresh token
        access_payload = {
            "sub": user_id,
            "iat": int(now.timestamp()),
            "exp": int(access_token_expiry.timestamp()),
            "type": TokenType.ACCESS.value,
            "jti": jti,
        }

        access_token = jwt.encode(
            access_payload,
            self.walter_sm.get_access_token_secret_key(),
            algorithm="HS256",
        )

        return access_token, access_token_expiry

    def hash_secret(self, secret: str) -> Tuple[bytes, bytes]:
        """
        Hash the given secret using bcrypt.

        This method just uses bcrypt: https://github.com/pyca/bcrypt

        Args:
            secret: The secret in plaintext before salting and hashing.

        Returns:
            salt, password_hash
        """
        if isinstance(secret, str) is False:
            raise TypeError("Password must be a string!")
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(secret.encode(), salt)
        return salt, password_hash

    def check_secret(self, secret: str, secret_hash: str) -> bool:
        """
        Checks if a given secret matches the given secret hash.

        Args:
            secret: The secret in plaintext to check.
            secret_hash: The hashed secret to check against.

        Returns:
            boolean: True if the given secret matches the given secret hash, False otherwise.
        """
        if isinstance(secret, str) is False or isinstance(secret_hash, str) is False:
            raise TypeError("Password and password hash must both be strings!")
        return bcrypt.checkpw(secret.encode(), secret_hash.encode())

    def get_bearer_token(self, event: dict) -> str | None:
        """
        Get the bearer token from the request event headers.

        Args:
            event: The request event for an API that requires a bearer token.

        Returns:
            The bearer token if found, else None.
        """
        if event["headers"] is None or "Authorization" not in event["headers"]:
            return None
        try:
            return event["headers"]["Authorization"].split(" ")[1]
        except Exception:
            log.error("Unexpected error occurred while parsing token!")
            return None

    @staticmethod
    def _generate_jti() -> str:
        """Generate JTI with timestamp and random component"""
        timestamp_part = int(datetime.now(timezone.utc).timestamp())
        random_part = "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(10)
        )
        return f"jti-{timestamp_part}{random_part}"
