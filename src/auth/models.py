from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TokenType(Enum):
    """Token Type"""

    ACCESS = "access"
    REFRESH = "refresh"

    @classmethod
    def from_string(cls, token_type: str):
        for token_type_enum in cls:
            if token_type_enum.value == token_type:
                return token_type_enum
        raise ValueError(f"Invalid token type: {token_type}")


@dataclass
class Tokens:
    """
    Represents authentication tokens for Walter's token-based session management.

    Walter uses a hybrid authentication approach that combines the scalability
    of JWTs with the security controls of session management:

    - Access tokens: Stateless JWTs for API authentication (short-lived)
    - Refresh tokens: Stateful session tokens for token renewal (long-lived)

    This provides session-like security controls (immediate revocation, logout)
    while maintaining the distributed benefits of JWT authentication.
    """

    jti: str
    access_token: str
    refresh_token: str
    access_token_expiry: datetime
    refresh_token_expiry: datetime
    revoked: bool = False

    def __post_init__(self) -> None:
        """
        Validate token attributes after initialization.

        Raises:
            ValueError: If either token is empty or None
        """
        if not self.access_token or not self.access_token.strip():
            raise ValueError("access_token cannot be empty or None")
        if not self.refresh_token or not self.refresh_token.strip():
            raise ValueError("refresh_token cannot be empty or None")

    def to_dict(self) -> dict:
        """
        Convert AuthTokens to dictionary representation.

        Useful for JSON serialization in API responses.

        Returns:
            dict: Dictionary with access_token and refresh_token keys
        """
        return {"access_token": self.access_token, "refresh_token": self.refresh_token}

    @classmethod
    def from_dict(cls, token_dict: dict) -> "Tokens":
        """
        Create AuthTokens instance from dictionary.

        Args:
            token_dict: Dictionary containing access_token and refresh_token keys

        Returns:
            AuthTokens: New instance with tokens from dictionary

        Raises:
            KeyError: If required keys are missing from dictionary
            ValueError: If token values are invalid

        Example:
            ```python
            data = {"access_token": "...", "refresh_token": "..."}
            tokens = AuthTokens.from_dict(data)
            ```
        """
        return cls(
            access_token=token_dict["access_token"],
            refresh_token=token_dict["refresh_token"],
        )

    def mask_for_logging(self) -> dict:
        """
        Create a safe representation for logging that masks sensitive token data.

        Returns only the first 8 and last 4 characters of each token for
        debugging purposes while maintaining security.

        Returns:
            dict: Dictionary with masked token values safe for logging
        """

        def mask_token(token: str) -> str:
            if len(token) <= 12:
                return "***"
            return f"{token[:8]}...{token[-4:]}"

        return {
            "access_token": mask_token(self.access_token),
            "refresh_token": mask_token(self.refresh_token),
        }
