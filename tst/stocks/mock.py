import json
from collections import defaultdict
from datetime import datetime as dt
from typing import List

from polygon import RESTClient
from polygon.rest.models import Agg
from pytest_mock import MockerFixture
from dataclasses import dataclass

from src.stocks.alphavantage.models import CompanyOverview
from tst.constants import PRICES_TEST_FILE, COMPANIES_TEST_FILE


@dataclass
class MockPolygon:
    """
    MockPolygon
    """

    mocker: MockerFixture

    def create_client(self) -> RESTClient:
        mock_polygon_rest_client = self.mocker.MagicMock(spec=RESTClient)
        mock_polygon_rest_client.list_aggs.side_effect = self._mock_prices
        return mock_polygon_rest_client

    def _mock_prices(self, *args, **kwargs) -> List[Agg]:
        mock_prices_by_stock = defaultdict(list)
        with open(PRICES_TEST_FILE) as prices_f:
            for price in prices_f:
                if not price.strip():
                    continue
                price_json = json.loads(price)
                stock = price_json["stock"]
                mock_prices_by_stock[stock].append(
                    Agg(
                        open=price_json["open"],
                        high=price_json["high"],
                        low=price_json["low"],
                        close=price_json["close"],
                        timestamp=dt.strptime(
                            price_json["timestamp"], "%Y-%m-%dT%H:%M:%SZ"
                        ).timestamp()
                        * 1000,
                    )
                )
        for key, value in kwargs.items():
            if key == "ticker":
                return mock_prices_by_stock[value]
        raise ValueError(f"Stock prices not mocked!\n{kwargs}")


@dataclass
class MockAlphaVantageClient:
    """
    MockAlphaVantageClientp
    """

    company_overviews_map: dict = None  # set during post-init

    def __post_init__(self):
        self.company_overview_map = {}
        with open(COMPANIES_TEST_FILE) as stocks_f:
            for stock in stocks_f:
                if not stock.strip():
                    continue
                stock_json = json.loads(stock)
                symbol = stock_json["symbol"]
                self.company_overview_map[symbol] = CompanyOverview(
                    symbol=symbol,
                    name=stock_json["company"],
                    description=stock_json["description"],
                    exchange=stock_json["exchange"],
                    sector=stock_json["sector"],
                    industry=stock_json["industry"],
                    official_site=stock_json["official_site"],
                    address=stock_json["address"],
                )

    def get_company_overview(self, symbol: str) -> CompanyOverview:
        return self.company_overview_map.get(symbol)
