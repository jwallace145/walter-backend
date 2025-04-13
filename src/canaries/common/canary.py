from abc import ABC, abstractmethod

from requests import Response

from src.api.common.models import Status
from src.canaries.common.models import CanaryResponse
from src.utils.log import Logger
import datetime as dt

log = Logger(__name__).get_logger()


class BaseCanary(ABC):
    """
    WalterCanary: BaseCanary

    This class contains the undifferentiated logic for a
    Walter canary. The purpose of a canary is to ensure
    all the various Walter APIs are working as expected.
    """

    def __init__(
        self,
        canary_name: str,
        api_url: str,
    ) -> None:
        self.canary_name = canary_name
        self.api_url = api_url

    def invoke(self) -> dict:
        log.info(f"Invoked '{self.canary_name}'!")

        start = dt.datetime.now(dt.UTC)
        response = self.call_api()
        end = dt.datetime.now(dt.UTC)

        log.info(f"API Response - Status Code: {response.status_code}")

        return CanaryResponse(
            canary_name=self.canary_name,
            status=(
                Status.SUCCESS if response.status_code in [200, 201] else Status.FAILURE
            ),
            response_time_millis=(end - start).total_seconds() * 1000,
        ).to_json()

    @abstractmethod
    def call_api(self) -> Response:
        pass
