from datetime import datetime as dt

import pytest
from polygon import RESTClient
from polygon.rest.models import Agg

from src.database.users.models import User
from src.database.userstocks.models import UserStock
from src.stocks.polygon.client import PolygonClient
from src.stocks.polygon.models import StockPrices, StockPrice
from tst.conftest import SECRETS_MANAGER_POLIGON_API_KEY_VALUE

WALTER = User(email="walter@gmail.com", username="walter")

AAPL = UserStock(user_email=WALTER.email, stock_symbol="AAPL", quantity=1.0)

START_DATE = dt(year=2024, month=10, day=1, hour=0, minute=0, second=0, microsecond=0)
END_DATE = dt(year=2024, month=10, day=1, hour=1, minute=0, second=0, microsecond=0)

STOCK_PRICES = StockPrices(
    prices=[
        StockPrice(symbol=AAPL.stock_symbol, price=100.0, timestamp=START_DATE),
        StockPrice(symbol=AAPL.stock_symbol, price=110.0, timestamp=END_DATE),
    ]
)


@pytest.fixture
def polygon_client(mocker) -> PolygonClient:
    mock_polygon_rest_client = mocker.MagicMock(spec=RESTClient)
    mock_polygon_rest_client.list_aggs.return_value = [
        Agg(
            open=100.0,
            high=110.0,
            low=90.0,
            close=100.0,
            volume=1000.0,
            vwap=100.0,  # lol no idea what this is
            timestamp=START_DATE.timestamp() * 1000,  # in epoch
            transactions=1,  # lol no idea what this is
            otc=None,
        ),
        Agg(
            open=110.0,
            high=110.0,
            low=90.0,
            close=100.0,
            volume=1000.0,
            vwap=100.0,  # lol no idea what this is
            timestamp=END_DATE.timestamp() * 1000,  # in epoch
            transactions=1,  # lol no idea what this is
            otc=None,
        ),
    ]
    return PolygonClient(
        api_key=SECRETS_MANAGER_POLIGON_API_KEY_VALUE, client=mock_polygon_rest_client
    )


def test_get_prices(polygon_client: PolygonClient) -> None:
    assert set(STOCK_PRICES.prices) == set(
        polygon_client.get_prices(AAPL, START_DATE, END_DATE).prices
    )
