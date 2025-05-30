from dataclasses import dataclass
from typing import Dict, List, Optional

from src.database.stocks.models import Stock
from src.database.userstocks.models import UserStock
from src.stocks.polygon.models import StockPrices


@dataclass(frozen=True)
class StockEquity:
    """
    StockEquity model class

    The stock model object returned for user stocks contained
    within their portfolio
    """

    symbol: str
    company: str
    sector: str
    price: float
    quantity: float
    equity: float
    icon_url: Optional[str] = None
    logo_url: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "company": self.company,
            "sector": self.sector,
            "price": self.price,
            "quantity": self.quantity,
            "equity": self.equity,
            "icon_url": self.icon_url,
            "logo_url": self.logo_url,
        }


@dataclass
class Portfolio:

    stocks: Dict[str, Stock]  # indexed by stock symbol
    user_stocks: Dict[str, UserStock]  # indexed by stock symbol
    prices: Dict[str, StockPrices]  # indexed by stock symbol

    def get_stock_symbols(self) -> List[str]:
        return list(self.user_stocks.keys())

    def get_stocks(self) -> List[UserStock]:
        return list(self.user_stocks.values())

    def get_latest_price(self, symbol: str) -> float:
        return self.prices[symbol].prices[-1].price

    def get_number_of_shares(self, symbol: str) -> float:
        return self.user_stocks[symbol].quantity

    def get_equity(self, symbol: str) -> float:
        price = self.get_latest_price(symbol)
        shares = self.get_number_of_shares(symbol)
        return price * shares

    def get_total_equity(self) -> float:
        equity = 0
        for stock in self.user_stocks.keys():
            equity += self.get_equity(stock)
        return equity

    def get_stock_equities(self) -> List[StockEquity]:
        stock_equities = []
        for stock in self.get_stock_symbols():
            company = self.stocks[stock].company
            sector = self.stocks[stock].sector
            price = self.get_latest_price(stock)
            quantity = self.get_number_of_shares(stock)
            icon_url = self.stocks[stock].icon_url
            logo_url = self.stocks[stock].logo_url
            equity = self.get_equity(stock)
            stock_equities.append(
                StockEquity(
                    stock, company, sector, price, quantity, equity, icon_url, logo_url
                )
            )
        return stock_equities
