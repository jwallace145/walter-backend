from dataclasses import dataclass

from polygon import BadResponse
from polygon.rest.models import TickerDetails

from src.database.securities.models import SecurityType
from datetime import datetime, timezone, timedelta
from typing import Dict

MOCK_DATA = {
    "AAPL": {
        "ticker": "AAPL",
        "name": "Apple Inc.",
        "exchange": "XNAS",
        "price": 100.00,
    },
    "COKE": {
        "ticker": "COKE",
        "name": "Coca-Cola Consolidated Inc.",
        "exchange": "XNYS",
        "price": 100.00,
    },
    "META": {
        "ticker": "BTC",
        "name": "Bitcoin",
        "price": 10000.00,
    },
    "BTC": {
        "ticker": "BTC",
        "name": "Bitcoin",
        "price": 10000.00,
    },
    "ETH": {
        "ticker": "BTC",
        "name": "Bitcoin",
        "price": 10000.00,
    },
}


@dataclass
class MockPolygonClient:
    """Mock Polygon Client"""

    data: Dict[str, dict] = None

    def __post_init__(self):
        if self.data is None:
            self.data = MOCK_DATA

    def get_ticker_info(
        self, security_ticker: str, security_type: SecurityType
    ) -> TickerDetails:
        if security_ticker.upper() not in self.data:
            raise BadResponse("Security not found")
        ticker_details = TickerDetails()
        ticker_details.ticker = security_ticker.upper()
        ticker_details.name = self.data[security_ticker.upper()]["name"]

        if security_type == SecurityType.STOCK:
            ticker_details.primary_exchange = self.data[security_ticker.upper()][
                "exchange"
            ]

        return ticker_details

    def get_latest_price(
        self,
        security_ticker: str,
        security_type: SecurityType,
        start_date: datetime = datetime.now(timezone.utc) - timedelta(days=1),
        end_date: datetime = datetime.now(timezone.utc),
    ) -> float:
        if security_ticker.upper() not in self.data:
            raise BadResponse("Security not found")
        return self.data[security_ticker.upper()]["price"]
