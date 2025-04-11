from dataclasses import dataclass
import requests
import json

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

        response = requests.post(
            url=AuthUserCanary.API_URL,
            data=json.dumps(
                {
                    "email": AuthUserCanary.USER_EMAIL,
                    "password": AuthUserCanary.USER_PASSWORD,
                }
            ),
            headers={"content-type": "application/json"},
        )

        log.info(
            f"API Response - Status Code: {response.status_code}, Response Body: {response.text}"
        )

        return {
            "statusCode": response.status_code,
        }
