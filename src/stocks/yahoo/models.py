from dataclasses import dataclass


@dataclass
class YahooFinanceStock:
    """
    Yahoo Finance Stock

    The model object for a stock retrieved from Yahoo Finance.
    """

    symbol: str
    sector: str
    industry: str
