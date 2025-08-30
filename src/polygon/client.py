from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from polygon import RESTClient
from polygon.rest.models import TickerDetails
from src.database.securities.models import SecurityType
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class PolygonClient:
    """
    Polygon Client (https://polygon.io/)
    """

    api_key: str
    client: RESTClient = None  # lazy init

    def __post_init__(self) -> None:
        log.debug(f"Creating {Domain.PRODUCTION.value} Polygon client")
        self.client = RESTClient(api_key=self.api_key)

    def get_ticker_info(
        self, security_ticker: str, security_type: SecurityType
    ) -> TickerDetails:
        log.info(f"Getting ticker info for {security_ticker} ({security_type.value})")
        ticker = PolygonClient._get_ticker(security_ticker, security_type)
        log.debug(f"Ticker: {ticker}")

        details = self.client.get_ticker_details(
            ticker,
        )

        return details

    def get_latest_price(
        self,
        security_ticker: str,
        security_type: SecurityType,
        start_date: datetime = datetime.now(timezone.utc) - timedelta(days=7),
        end_date: datetime = datetime.now(timezone.utc),
    ) -> float:
        ticker = PolygonClient._get_ticker(security_ticker, security_type)

        aggs = []
        for a in self.client.list_aggs(
            ticker,
            1,
            "hour",
            start_date,
            end_date,
            adjusted="true",
            sort="asc",
        ):
            aggs.append(a)

        # TODO: Upgrade to Polygon premium and use latest trade API for price estimates (more accurate)

        # return the latest open price as surrogate for latest price
        return aggs[-1].open

    @staticmethod
    def _get_ticker(security_ticker: str, security_type: SecurityType) -> str:
        match security_type:
            case SecurityType.CRYPTO:
                return f"X:{security_ticker.upper()}USD"
            case SecurityType.STOCK:
                return security_ticker.upper()
