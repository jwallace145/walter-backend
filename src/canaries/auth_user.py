import datetime as dt
from dataclasses import dataclass

import requests

from src.api.common.models import Status
from src.canaries.common.models import CanaryResponse
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class AuthUserCanary:
    """
    WalterCanary: AuthUserCanary

    This canary calls the AuthUser API and ensures
    the canary user is able to authenticate successfully.
    """

    CANARY_NAME = "AuthUserCanary"
    API_URL = "https://084slq55lk.execute-api.us-east-1.amazonaws.com/dev/auth"
    USER_EMAIL = "canary@walterai.dev"
    USER_PASSWORD = "CanaryPassword1234&"

    def __post_init__(self) -> None:
        log.debug(f"Initializing {AuthUserCanary.CANARY_NAME}")

    def invoke(self) -> dict:
        log.info(f"Invoked '{AuthUserCanary.CANARY_NAME}'!")

        start = dt.datetime.now(dt.UTC)

        response = requests.post(
            url=AuthUserCanary.API_URL,
            json={
                "email": AuthUserCanary.USER_EMAIL,
                "password": AuthUserCanary.USER_PASSWORD,
            },
            headers={"content-type": "application/json"},
        )

        end = dt.datetime.now(dt.UTC)

        log.info(
            f"API Response - Status Code: {response.status_code}, Response Body: {response.text}"
        )

        return CanaryResponse(
            canary_name=AuthUserCanary.CANARY_NAME,
            status=Status.SUCCESS if response.status_code == 200 else Status.FAILURE,
            response_time_millis=(end - start).total_seconds() * 1000,
        ).to_json()
