from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
from requests import Response

from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class WebScraper:
    """
    This class uses BeautifulSoup to scrape the text contents
    web pages given by their URL.

    https://www.crummy.com/software/BeautifulSoup/bs4/doc/
    """

    def __post_init__(self):
        log.debug("Initializing WebScraper")

    def scrape(self, url: str) -> str | None:
        log.debug(f"Scraping text contents from web page with URL: '{url}'")

        response = self._get_response(url)
        if response is None:
            return None

        return self._parse_response(response)

    def _get_response(self, url: str) -> Response | None:
        log.debug(f"Getting response from web page with URL: '{url}'")
        try:
            return requests.get(url)
        except Exception:
            log.error(
                f"Unexpected error occurred getting response from web page with URL: '{url}'"
            )
            return None

    def _parse_response(self, response: Response) -> str | None:
        log.debug(f"Parsing response:\n{response}")
        soup = BeautifulSoup(response.text, "html.parser")
        for script in soup(
            ["script", "style", "footer", "nav", "header", "aside", "advertisement"]
        ):
            script.decompose()
        page_text = soup.get_text(strip=True)
        cleaned_text = " ".join(page_text.split())
        return cleaned_text
