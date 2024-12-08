from dataclasses import dataclass
import yfinance as yf

from src.stocks.yahoo.models import YahooFinanceStock
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class YahooFinanceClient:
    """
    Yahoo Finance Client
    """

    def __post_init__(self) -> None:
        log.debug("Creating YahooFinanceClient")

    def get_stock(self, symbol: str) -> YahooFinanceStock:
        log.info(f"Getting stock '{symbol}'")
        stock_info = yf.Ticker(symbol).info
        return YahooFinanceStock(
            symbol=symbol,
            sector=stock_info.get("sector", "N/A"),
            industry=stock_info.get("industry", "N/A"),
        )
