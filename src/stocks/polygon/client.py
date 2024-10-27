from dataclasses import dataclass
from datetime import datetime, timedelta, UTC
from typing import Dict, List

import polygon.exceptions
from polygon import RESTClient
from polygon.rest.models.aggs import Agg

from src.database.stocks.models import Stock
from src.database.userstocks.models import UserStock
from src.environment import Domain
from src.stocks.polygon.models import StockPrice, StockPrices, StockNews
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class PolygonClient:
    """
    Polygon Client (https://polygon.io/)

    The Polygon Client is used to interact with the Polygon API to get
    market data about users' stocks. This includes pricing data and
    current news as well. The data returned from Polygon is included
    in the context given to the LLMs to help write tailored newsletters
    for users with the latest prices and relevant news.
    """

    MAX_AGGREGATE_DATA_LIMIT = 50000

    api_key: str
    client: RESTClient = None  # lazy init

    def __post_init__(self) -> None:
        log.debug(f"Creating {Domain.PRODUCTION.value} Polygon client")

    def get_stock(self, symbol: str) -> Stock | None:
        self._init_rest_client()
        try:
            details = self.client.get_ticker_details(ticker=symbol)
            return Stock(symbol=details.ticker, company=details.name)
        except polygon.BadResponse:
            log.info(f"{symbol} does not exist in Polygon!")
            return None

    def batch_get_prices(
        self, stocks: Dict[str, UserStock], start_date: datetime, end_date: datetime
    ) -> Dict[str, StockPrices]:
        """
        This method gets prices from Polygon for a batch of stocks over the given timeframe.

        https://polygon.io/docs/stocks/get_v2_aggs_ticker__stocksticker__range__multiplier___timespan___from___to

        Args:
            stocks: The stocks to get pricing data from Polygon.
            start_date: The start date of the query.
            end_date: The end date of the query.

        Returns:
            The prices over the given timeframe for the batch of stocks.
        """
        self._init_rest_client()

        prices = {}
        for stock in stocks.values():
            prices[stock.stock_symbol] = self.get_prices(stock, start_date, end_date)

        return prices

    def get_prices(
        self, stock: UserStock, start_date: datetime, end_date: datetime
    ) -> StockPrices:
        """
        This method gets prices from Polygon for a single stock over the given timeframe.

        https://polygon.io/docs/stocks/get_v2_aggs_ticker__stocksticker__range__multiplier___timespan___from___to

        Args:
            stock: The stock to get pricing data from Polygon.
            start_date: The start date of the query to get pricing data.
            end_date: The end date of the query to get pricing data.

        Returns:
            The prices for the stock over the given timeframe.
        """
        self._init_rest_client()

        log.info(
            f"Getting aggregate data for '{stock.stock_symbol}' from '{start_date}' to '{end_date}'"
        )

        if start_date >= end_date:
            raise ValueError(
                f"start date '{start_date}' is after end date '{end_date}'!"
            )

        prices = []
        for agg in self.client.list_aggs(
            ticker=stock.stock_symbol,
            multiplier=1,
            timespan="hour",
            from_=PolygonClient._convert_date_to_string(start_date),
            to=PolygonClient._convert_date_to_string(end_date),
            limit=PolygonClient.MAX_AGGREGATE_DATA_LIMIT,
        ):
            prices.append(
                PolygonClient._convert_agg_to_stock_price(stock.stock_symbol, agg)
            )

        log.info(f"Successfully returned {len(prices)} prices")

        return StockPrices(prices)

    def get_stock_prices(
        self,
        stock: str,
        start_date: datetime = datetime.now(UTC) - timedelta(days=7),
        end_date: datetime = datetime.now(UTC),
    ) -> StockPrices:
        """
        Get stock prices for a single stock over the given timeframe.

        Args:
            stock: The stock symbol.
            start_date: The start date of the query.
            end_date: The end date of the query.

        Returns:
            stock prices for the stock over the given timeframe.
        """
        self._init_rest_client()

        log.info(
            f"Getting pricing data for '{stock}' from '{start_date}' to '{end_date}'"
        )

        if start_date >= end_date:
            raise ValueError(
                f"start date '{start_date}' is after end date '{end_date}'!"
            )

        prices = []
        for agg in self.client.list_aggs(
            ticker=stock,
            multiplier=1,
            timespan="hour",
            from_=PolygonClient._convert_date_to_string(start_date),
            to=PolygonClient._convert_date_to_string(end_date),
            limit=PolygonClient.MAX_AGGREGATE_DATA_LIMIT,
        ):
            prices.append(PolygonClient._convert_agg_to_stock_price(stock, agg))

        log.info(f"Successfully returned {len(prices)} prices")

        return StockPrices(prices)

    def batch_get_news(
        self, stocks: Dict[str, UserStock], latest_published_date: datetime
    ) -> Dict[str, List[StockNews]]:
        news = {}
        for stock in stocks.values():
            news[stock.stock_symbol] = self.get_news(stock, latest_published_date)
        return news

    def get_news(self, stock: str, latest_published_date: datetime) -> StockNews:
        """
        Get relevant news for the given stock over the timeframe.

        https://polygon.io/docs/stocks/get_v2_reference_news

        Args:
            stock:
            latest_published_date:

        Returns:

        """
        self._init_rest_client()

        log.info(
            f"Getting news for '{stock.stock_symbol}' with a latest published date of '{latest_published_date}'"
        )

        descriptions = []
        for n in self.client.list_ticker_news(
            ticker=stock.stock_symbol,
            published_utc_gt=PolygonClient._convert_date_to_string(
                latest_published_date
            ),
            limit=10,
        ):
            descriptions.append(n.description)
        return StockNews(symbol=stock.stock_symbol, descriptions=descriptions)

    def _init_rest_client(self) -> RESTClient:
        # lazy init polygon rest client
        if self.client is None:
            self.client = RESTClient(api_key=self.api_key)
        return self.client

    @staticmethod
    def _convert_date_to_string(date: datetime) -> str:
        return datetime.strftime(date, "%Y-%m-%d")

    @staticmethod
    def _convert_agg_to_stock_price(symbol: str, agg: Agg) -> StockPrice:
        return StockPrice(
            symbol=symbol,
            price=agg.open,
            timestamp=datetime.fromtimestamp(agg.timestamp / 1000),
        )
