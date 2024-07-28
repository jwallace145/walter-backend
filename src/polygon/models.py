from dataclasses import dataclass, field
from datetime import datetime


@dataclass(order=True)
class StockPrice:
    sort_index: int = field(init=False)
    symbol: str
    price: float
    timestamp: datetime

    def __post_init__(self) -> None:
        self.sort_index = self.timestamp
