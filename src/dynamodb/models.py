from dataclasses import dataclass


@dataclass
class User:
    email: str
    username: str

    def to_ddb_item(self) -> dict:
        return {
            "email": {
                "S": self.email,
            },
            "username": {"S": self.username},
        }


@dataclass
class Stock:
    symbol: str
    company: str

    def to_ddb_item(self) -> dict:
        return {
            "symbol": {
                "S": self.symbol,
            },
            "company": {"S": self.company},
        }


@dataclass
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
