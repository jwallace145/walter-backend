import datetime as dt
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class UserStock:
    """
    UserStock Model

    This class is responsible for maintaining the many-to-many relationship between
    users and stocks. This model contains user to stock mappings with each of their
    primary keys to store user portfolios.
    """

    user_id: str
    stock_symbol: str
    quantity: float
    timestamp: dt.datetime = dt.datetime.now(dt.UTC)

    def to_ddb_item(self) -> dict:
        return {
            "user_id": {
                "S": self.user_id,
            },
            "stock_symbol": {"S": self.stock_symbol},
            "quantity": {"S": str(self.quantity)},
            "timestamp": {"S": self.timestamp.isoformat()},
        }

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "stock_symbol": self.stock_symbol,
            "quantity": self.quantity,
            "timestamp": self.timestamp.isoformat(),
        }

    def __str__(self) -> str:
        return json.dumps(
            {
                "user_id": self.user_id,
                "stock": self.stock_symbol,
                "quantity": self.quantity,
                "timestamp": self.timestamp.isoformat(),
            }
        )
