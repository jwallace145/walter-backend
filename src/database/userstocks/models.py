from dataclasses import dataclass


@dataclass(frozen=True)
class UserStock:
    user_email: str
    stock_symbol: str

    def to_ddb_item(self) -> dict:
        return {
            "user_email": {
                "S": self.user_email,
            },
            "stock_symbol": {"S": self.stock_symbol},
        }
