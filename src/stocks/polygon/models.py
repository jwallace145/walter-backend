from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass(order=True)
class StockPrice:
    sort_index: int = field(
        init=False
    )  # allows class to be sorted given the sort index

    symbol: str
    price: float
    timestamp: datetime

    def __post_init__(self) -> None:
        self.sort_index = self.timestamp


@dataclass
class StockPrices:

    prices: List[StockPrice]

    def get_latest_price(self) -> float:
        return self.prices[-1].price
