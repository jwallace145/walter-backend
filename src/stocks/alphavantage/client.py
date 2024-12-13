import json
from dataclasses import dataclass

import requests

from src.stocks.alphavantage.models import CompanyOverview
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class AlphaVantageClient:
    """
    AlphaVantage Client

    docs: https://www.alphavantage.co/documentation/
    """

    URL = "https://www.alphavantage.co"

    api_key: str

    def __post_init__(self) -> None:
        log.debug("Initializing AlphaVantage Client")

    def get_company_overview(self, symbol: str) -> CompanyOverview:
        """
        Get the company overview.

        Args:
            symbol: The stock symbol of the company.

        Returns:
            The company overview.
        """
        log.info(f"Getting company overview for '{symbol}'")
        url = self.get_company_overview_url(symbol)
        response = requests.get(url).json()

        # if empty dict response from alpha vantage then assume stock does not exist
        if response == {}:
            return None

        overview = CompanyOverview(
            symbol=response["Symbol"],
            name=response["Name"],
            description=response["Description"],
            exchange=response["Exchange"],
            sector=response["Sector"],
            industry=response["Industry"],
            official_site=response["OfficialSite"],
        )
        log.info(
            f"Returned company overview for '{symbol}':\n{json.dumps(overview.to_dict(), indent=2)}"
        )

        return overview

    def get_company_overview_url(self, symbol: str) -> str:
        return f"{AlphaVantageClient.URL}/query?function=OVERVIEW&symbol={symbol}&apikey={self.api_key}/"
