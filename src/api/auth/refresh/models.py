from dataclasses import dataclass
from datetime import datetime


@dataclass
class RefreshResponseData:
    """Refresh Response"""

    user_id: str
    access_token_expiration: datetime

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "access_token_expires_at": self.access_token_expiration.isoformat(),
        }
