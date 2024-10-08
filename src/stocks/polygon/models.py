from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass(frozen=True, order=True)
class StockPrice:
    symbol: str = field(compare=False)
    price: float = field(compare=False)
    timestamp: datetime = field(compare=True)


@dataclass
class StockPrices:

    prices: List[StockPrice]

    def get_latest_price(self) -> float:
        return self.prices[-1].price


@dataclass(frozen=True)
class StockNews:
    symbol: str
    descriptions: List[str]
