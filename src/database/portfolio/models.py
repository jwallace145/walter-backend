from dataclasses import dataclass
from typing import List

from src.stocks.models import StockEquity
import datetime as dt


@dataclass
class Portfolio:
    """
    WalterDB: Portfolio model
    """

    account_id: str
    portfolio_id: str
    stocks: List[StockEquity]
    created_at: dt.datetime
    updated_at: dt.datetime
    balance: float = None  # set during post-init

    def __post_init__(self) -> None:
        self.balance = sum([stock.equity for stock in self.stocks])

    def to_dict(self) -> dict:
        return {
            "account_id": self.account_id,
            "portfolio_id": self.portfolio_id,
            "balance": self.balance,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "stocks": [stock.to_dict() for stock in self.stocks],
        }
