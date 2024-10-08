from datetime import datetime as dt
from datetime import timedelta
from typing import List

import pytest
from polygon import RESTClient
from polygon.rest.models import Agg, TickerNews

from src.database.stocks.models import Stock
from src.database.users.models import User
from src.database.userstocks.models import UserStock
from src.stocks.client import WalterStocksAPI
from src.stocks.models import Portfolio
from src.stocks.polygon.client import PolygonClient
from src.stocks.polygon.models import StockPrices, StockPrice, StockNews
from tst.conftest import SECRETS_MANAGER_POLIGON_API_KEY_VALUE

WALTER = User(email="walter@gmail.com", username="walter")

START_DATE = dt(year=2024, month=10, day=1, hour=0, minute=0, second=0, microsecond=0)
END_DATE = dt(year=2024, month=10, day=1, hour=2, minute=0, second=0, microsecond=0)

AAPL = Stock(symbol="AAPL", company="Apple")
META = Stock(symbol="META", company="Facebook")

STOCKS = {
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
                timestamp=START_DATE + timedelta(hours=1),
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
                timestamp=START_DATE + timedelta(hours=1),
            ),
            StockPrice(
                symbol=META.symbol,
                price=250.0,
                timestamp=END_DATE,
            ),
        ]
    ),
}

NEWS = {
    AAPL.symbol: StockNews(
        symbol=AAPL.symbol, descriptions=["It is much bigger than Atlantis!"]
    ),
    META.symbol: StockNews(
        symbol=META.symbol,
        descriptions=[
            "The croissant weights over 500 pounds!",
            "Uh oh, a lot of people are going to be in trouble!",
        ],
    ),
}

PORTFOLIO = Portfolio(STOCKS, PRICES, NEWS)


@pytest.fixture
def walter_stocks_api(mocker) -> WalterStocksAPI:
    mock_polygon_rest_client = mocker.MagicMock(spec=RESTClient)

    def mock_aggs(*args, **kwargs) -> List[Agg]:
        aggs = {
            AAPL.symbol: [
                Agg(
                    open=90.0,
                    high=100.0,
                    low=85.0,
                    close=95.0,
                    timestamp=START_DATE.timestamp() * 1000,
                ),
                Agg(
                    open=95.0,
                    high=100.0,
                    low=90.0,
                    close=100.0,
                    timestamp=(START_DATE + timedelta(hours=1)).timestamp() * 1000,
                ),
                Agg(
                    open=100.0,
                    high=120.0,
                    low=95.0,
                    close=105.0,
                    timestamp=END_DATE.timestamp() * 1000,
                ),
            ],
            META.symbol: [
                Agg(
                    open=200.0,
                    high=220.0,
                    low=190.0,
                    close=210.0,
                    timestamp=START_DATE.timestamp() * 1000,
                ),
                Agg(
                    open=225.0,
                    high=240.0,
                    low=220.0,
                    close=230.0,
                    timestamp=(START_DATE + timedelta(hours=1)).timestamp() * 1000,
                ),
                Agg(
                    open=250.0,
                    high=255.0,
                    low=245.0,
                    close=250.0,
                    timestamp=END_DATE.timestamp() * 1000,
                ),
            ],
        }
        for key, value in kwargs.items():
            if key == "ticker":
                return aggs[value]
        raise ValueError("ticker not in get aggs kwargs!")

    mock_polygon_rest_client.list_aggs.side_effect = mock_aggs

    def mock_ticker_news(*args, **kwargs) -> List[TickerNews]:
        news = {
            AAPL.symbol: [
                TickerNews(
                    author="Maya Grayson",
                    title="Scientists Discover Hidden Underwater City Off the Coast of Australia",
                    description="It is much bigger than Atlantis!",
                )
            ],
            META.symbol: [
                TickerNews(
                    author="Ethan Caldwell",
                    title="Local Bakery Breaks World Record for Largest Croissant Ever Made",
                    description="The croissant weights over 500 pounds!",
                ),
                TickerNews(
                    author="Lila Montgomery",
                    title="Tech Giant Unveils Revolutionary Smart Glasses That Can Read Your Thoughts",
                    description="Uh oh, a lot of people are going to be in trouble!",
                ),
            ],
        }
        for key, value in kwargs.items():
            if key == "ticker":
                return news[value]
        raise ValueError("ticker not in list ticker news kwargs!")

    mock_polygon_rest_client.list_ticker_news.side_effect = mock_ticker_news

    return WalterStocksAPI(
        client=PolygonClient(
            api_key=SECRETS_MANAGER_POLIGON_API_KEY_VALUE,
            client=mock_polygon_rest_client,
        )
    )


def test_get_portfolio(walter_stocks_api: WalterStocksAPI) -> None:
    assert PORTFOLIO == walter_stocks_api.get_portfolio(STOCKS, START_DATE, END_DATE)


def test_get_stocks() -> None:
    assert {AAPL.symbol, META.symbol} == set(PORTFOLIO.get_stocks())


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
