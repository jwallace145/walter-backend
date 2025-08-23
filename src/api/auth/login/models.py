from dataclasses import dataclass

from src.auth.models import Tokens
from src.database.users.models import User


@dataclass
class LoginResponse:

    user: User
    tokens: Tokens

    def to_dict(self) -> dict:
        return {
            "user_id": self.user.user_id,
            "access_token": self.tokens.access_token,
            "refresh_token": self.tokens.refresh_token,
            "access_token_expires_at": self.tokens.access_token_expiry.isoformat(),
            "refresh_token_expires_at": self.tokens.refresh_token_expiry.isoformat(),
        }
