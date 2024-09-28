from dataclasses import dataclass


@dataclass
class UserStock:
    user_email: str
    stock_symbol: str
