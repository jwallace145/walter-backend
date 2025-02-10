import datetime as dt
from dataclasses import dataclass
from typing import Tuple

import bcrypt
import jwt

from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class WalterAuthenticator:
    """
    Walter Authenticator
    """

    walter_sm: WalterSecretsManagerClient

    def generate_user_token(self, email: str) -> str:
        """
        Generate JSON web token for user.

        After a user successfully authenticates themselves via login, Walter creates
        a token to give to the user to verify their identity. This allows the user
        to make subsequent authenticated requests. The token is generated via JSON
        web tokens with the algorithm specified in Walter's configs.

        Args:
            email: The user email to generate the identity token.

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
            self.walter_sm.get_jwt_secret_key(),
            algorithm="HS256",
        )

    def decode_user_token(self, token: str) -> bool | None:
        """
        Decode the given user token to verify user identity.

        Args:
            token: The user identity token

        Returns:
            True if the token is valid, False otherwise.
        """
        try:
            return jwt.decode(
                token,
                self.walter_sm.get_jwt_secret_key(),
                algorithms=["HS256"],
            )
        except jwt.ExpiredSignatureError:
            log.error("Token has expired!")
            return None
        except jwt.InvalidTokenError:
            log.error("Invalid token!")
            return None

    def generate_email_token(self, email: str) -> str:
        """
        Generate JSON web token for email verification purposes.

        To verify a user email, Walter sends a verification email to the given
        email address. The email contains the email identity token that can then
        be used to verify the address via a link in the email. This ensures
        subscribed users actually have access to the emails they provided.

        Args:
            email: The candidate user email address for verification.

        Returns:
            The unique JSON web token for the email address.
        """
        now = dt.datetime.now(dt.UTC)
        return jwt.encode(
            {
                "sub": email,
                "iat": now,
                "exp": now + dt.timedelta(days=7),
            },
            self.walter_sm.get_jwt_verify_email_secret_key(),
            algorithm="HS256",
        )

    def decode_email_token(self, token: str) -> bool:
        """
        Decode the email verification token to verify user ownership.

        If a user can provide a valid email verification JSON web token, the email address
        can be set to verified and Walter can start sending newsletters to the user.

        Args:
            token: The email verification JSON web token to decode.

        Returns:
            True if the token is valid, False otherwise.
        """
        try:
            return jwt.decode(
                token,
                self.walter_sm.get_jwt_verify_email_secret_key(),
                algorithms=["HS256"],
            )
        except jwt.ExpiredSignatureError:
            log.error("Token has expired!")
            return None
        except jwt.InvalidTokenError:
            log.error("Invalid token!")
            return None

    def generate_change_password_token(self, email: str) -> str:
        """
        Generate JSON web token for changing user password purposes.

        Users can change their passwords if they forgot them by having
        Walter send an email to their email address that contains a token
        in a URL to change their password. This method generates the change
        password tokens.

        Args:
            email: The email address of the user to change password.

        Returns:
            The unique JSON web token for changing the user's password.
        """
        now = dt.datetime.now(dt.UTC)
        return jwt.encode(
            {
                "sub": email,
                "iat": now,
                "exp": now + dt.timedelta(days=7),
            },
            self.walter_sm.get_jwt_change_password_secret_key(),
            algorithm="HS256",
        )

    def decode_change_password_token(self, token: str) -> bool:
        """
        Decode the change password token to ensure change password request is authenticated.

        This method decodes the change password token given to users attempting
        to change their password.This method ensures requests to change a password
        are valid and authenticated.

        Args:
            token: The change password JSON web token to decode.

        Returns:
            True if the token is valid, False otherwise.
        """
        try:
            return jwt.decode(
                token,
                self.walter_sm.get_jwt_change_password_secret_key(),
                algorithms=["HS256"],
            )
        except jwt.ExpiredSignatureError:
            log.error("Token has expired!")
            return None
        except jwt.InvalidTokenError:
            log.error("Invalid token!")
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
        """
        Get the user identity token from the request event for authenticated APIs.

        Args:
            event: The request event for authenticated APIs that require user identity tokens.

        Returns:
            The user identity token if provided, else None.
        """
        if event["headers"] is None or "Authorization" not in event["headers"]:
            return None
        return event["headers"]["Authorization"].split(" ")[1]
