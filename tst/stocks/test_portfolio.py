import pytest

from src.database.stocks.models import Stock
from src.database.users.models import User
from src.database.userstocks.models import UserStock
from src.stocks.models import Portfolio
from src.stocks.polygon.models import StockPrices, StockPrice
from datetime import datetime as dt

WALTER = User(email="walter@gmail.com", username="walter")

AAPL = Stock(symbol="AAPL", company="Apple")
META = Stock(symbol="META", company="Facebook")
NFLX = Stock(symbol="NFLX", company="Netflix")

STOCKS = {
    AAPL.symbol: UserStock(
        user_email=WALTER.email, stock_symbol=AAPL.symbol, quantity=1.0
    ),
    META.symbol: UserStock(
        user_email=WALTER.email, stock_symbol=META.symbol, quantity=2.0
    ),
    NFLX.symbol: UserStock(
        user_email=WALTER.email, stock_symbol=NFLX.symbol, quantity=3.0
    ),
}

TIMESTAMP_1 = dt(year=2024, month=10, day=1, hour=0, minute=0, second=0, microsecond=0)
TIMESTAMP_2 = dt(year=2024, month=10, day=1, hour=1, minute=0, second=0, microsecond=0)
TIMESTAMP_3 = dt(year=2024, month=10, day=1, hour=2, minute=0, second=0, microsecond=0)

PRICES = {
    AAPL.symbol: StockPrices(
        prices=[
            StockPrice(symbol=AAPL.symbol, price=90.0, timestamp=TIMESTAMP_1),
            StockPrice(symbol=AAPL.symbol, price=95.0, timestamp=TIMESTAMP_2),
            StockPrice(symbol=AAPL.symbol, price=100.0, timestamp=TIMESTAMP_3),
        ]
    ),
    META.symbol: StockPrices(
        prices=[
            StockPrice(symbol=META.symbol, price=200.0, timestamp=TIMESTAMP_1),
            StockPrice(symbol=META.symbol, price=225.0, timestamp=TIMESTAMP_2),
            StockPrice(symbol=META.symbol, price=250.0, timestamp=TIMESTAMP_3),
        ]
    ),
    NFLX.symbol: StockPrices(
        prices=[
            StockPrice(symbol=NFLX.symbol, price=550.0, timestamp=TIMESTAMP_1),
            StockPrice(symbol=NFLX.symbol, price=525.0, timestamp=TIMESTAMP_2),
            StockPrice(symbol=NFLX.symbol, price=500.0, timestamp=TIMESTAMP_3),
        ]
    ),
}


@pytest.fixture
def portfolio() -> Portfolio:
    return Portfolio(stocks=STOCKS, prices=PRICES)


def test_get_stocks(portfolio: Portfolio) -> None:
    assert {AAPL.symbol, META.symbol, NFLX.symbol} == set(portfolio.get_stocks())


def test_get_latest_price(portfolio: Portfolio) -> None:
    assert 100.0 == portfolio.get_latest_price(AAPL.symbol)
    assert 250.0 == portfolio.get_latest_price(META.symbol)
    assert 500.0 == portfolio.get_latest_price(NFLX.symbol)


def test_get_number_of_shares(portfolio: Portfolio) -> None:
    assert 1.0 == portfolio.get_number_of_shares(AAPL.symbol)
    assert 2.0 == portfolio.get_number_of_shares(META.symbol)
    assert 3.0 == portfolio.get_number_of_shares(NFLX.symbol)


def test_get_equity(portfolio: Portfolio) -> None:
    assert 100.0 == portfolio.get_equity(AAPL.symbol)
    assert 500.0 == portfolio.get_equity(META.symbol)
    assert 1500.0 == portfolio.get_equity(NFLX.symbol)


def test_get_total_equity(portfolio: Portfolio) -> None:
    assert 2100.0 == portfolio.get_total_equity()
