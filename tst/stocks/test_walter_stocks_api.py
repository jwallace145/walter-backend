import datetime as dt

from src.database.stocks.models import Stock
from src.database.users.models import User
from src.database.userstocks.models import UserStock
from src.stocks.client import WalterStocksAPI
from src.stocks.models import Portfolio
from src.stocks.polygon.models import StockPrices, StockPrice

WALTER = User(email="walter@gmail.com", username="walter", password_hash="password")

START_DATE = dt.datetime(
    year=2025, month=1, day=1, hour=1, minute=0, second=0, microsecond=0
)
END_DATE = dt.datetime(
    year=2025, month=1, day=1, hour=3, minute=0, second=0, microsecond=0
)


AAPL = Stock(symbol="AAPL", company="Apple")
META = Stock(symbol="META", company="Facebook")

USER_STOCKS = {
    AAPL.symbol: UserStock(
        user_email=WALTER.email, stock_symbol=AAPL.symbol, quantity=1.0
    ),
    META.symbol: UserStock(
        user_email=WALTER.email, stock_symbol=META.symbol, quantity=2.0
    ),
}

PRICES = {
    AAPL.symbol: StockPrices(
        prices=[
            StockPrice(
                symbol=AAPL.symbol,
                price=90.0,
                timestamp=START_DATE,
            ),
            StockPrice(
                symbol=AAPL.symbol,
                price=95.0,
                timestamp=START_DATE + dt.timedelta(hours=1),
            ),
            StockPrice(
                symbol=AAPL.symbol,
                price=100.0,
                timestamp=END_DATE,
            ),
        ]
    ),
    META.symbol: StockPrices(
        prices=[
            StockPrice(
                symbol=META.symbol,
                price=200.0,
                timestamp=START_DATE,
            ),
            StockPrice(
                symbol=META.symbol,
                price=225.0,
                timestamp=START_DATE + dt.timedelta(hours=1),
            ),
            StockPrice(
                symbol=META.symbol,
                price=250.0,
                timestamp=END_DATE,
            ),
        ]
    ),
}

STOCKS = {AAPL.symbol: AAPL, META.symbol: META}

PORTFOLIO = Portfolio(STOCKS, USER_STOCKS, PRICES)


def test_does_stock_exist(walter_stocks_api: WalterStocksAPI) -> None:
    assert walter_stocks_api.get_stock(AAPL.symbol) is not None
    assert walter_stocks_api.get_stock(META.symbol) is not None
    assert walter_stocks_api.get_stock("INVALID") is None


def test_get_portfolio(walter_stocks_api: WalterStocksAPI) -> None:
    assert PORTFOLIO == walter_stocks_api.get_portfolio(
        USER_STOCKS, STOCKS, START_DATE, END_DATE
    )


def test_get_stocks() -> None:
    assert {AAPL.symbol, META.symbol} == set(PORTFOLIO.get_stock_symbols())


def test_get_latest_price() -> None:
    assert 100.0 == PORTFOLIO.get_latest_price(AAPL.symbol)
    assert 250.0 == PORTFOLIO.get_latest_price(META.symbol)


def test_get_number_of_shares() -> None:
    assert 1.0 == PORTFOLIO.get_number_of_shares(AAPL.symbol)
    assert 2.0 == PORTFOLIO.get_number_of_shares(META.symbol)


def test_get_equity() -> None:
    assert 100.0 == PORTFOLIO.get_equity(AAPL.symbol)
    assert 500.0 == PORTFOLIO.get_equity(META.symbol)


def test_get_total_equity() -> None:
    assert 600.0 == PORTFOLIO.get_total_equity()
