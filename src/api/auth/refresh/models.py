from dataclasses import dataclass
from datetime import datetime


@dataclass
class RefreshResponseData:
    """Refresh Response"""

    access_token: str
    access_token_expiration: datetime

    def to_dict(self) -> dict:
        return {
            "access_token": self.access_token,
            "access_token_expiration": self.access_token_expiration.isoformat(),
        }
