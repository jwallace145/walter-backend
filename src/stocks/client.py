import datetime as dt
from dataclasses import dataclass

from src.stocks.polygon.client import PolygonClient
from src.stocks.polygon.models import StockPrices
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class WalterStocksAPI:
    """
    WalterStocksAPI
    """

    polygon: PolygonClient

    def __post_init__(self) -> None:
        log.debug("Creating WalterStocksAPI")

    def get_prices(
        self, stock: str, start_date: dt.datetime, end_date: dt.datetime
    ) -> StockPrices:
        return self.polygon.get_stock_prices(stock, start_date, end_date)

    def get_latest_price(self, stock: str) -> float:
        now = dt.datetime.now()
        return self.get_prices(stock, now - dt.timedelta(days=7), now).prices[-1].price
