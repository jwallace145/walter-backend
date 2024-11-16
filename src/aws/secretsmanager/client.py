import json
from dataclasses import dataclass

from mypy_boto3_secretsmanager import SecretsManagerClient

from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class WalterSecretsManagerClient:
    """
    WalterSecretsManagerClient

    This client is responsible for retrieving secrets from SecretsManager used for
    generating/decoding authentication tokens and calling external APIs.

    Secrets:
        - PolygonAPIKey: The API key to access Polygon API for market data.
        - JWTSecretKey: The JSON web token (JWT) secret key used to verify user identity.
        - JWTVerifyEmailSecretKey: The JSON web token (JWT) secret key used to verify user emails.
    """

    POLYGON_API_KEY_SECRET_ID = "PolygonAPIKey"
    POLYGON_API_KEY_SECRET_NAME = "POLYGON_API_KEY"
    JWT_SECRET_KEY_SECRET_ID = "JWTSecretKey"
    JWT_SECRET_KEY_SECRET_NAME = "JWT_SECRET_KEY"
    JWT_VERIFY_EMAIL_SECRET_KEY_ID = "JWTVerifyEmailSecretAccessKey"
    JWT_VERIFY_EMAIL_SECRET_KEY_NAME = "JWTVerifyEmailSecretKey"

    client: SecretsManagerClient
    domain: Domain

    # lazy init all secrets
    polygon_api_key: str = None
    jwt_secret_key: str = None
    jwt_verify_email_secret_key: str = None

    def __post_init__(self) -> None:
        log.debug(
            f"Creating {self.domain.value} SecretsManager client in region '{self.client.meta.region_name}'"
        )

    def get_polygon_api_key(self) -> str:
        if self.polygon_api_key is None:
            self.polygon_api_key = self._get_secret(
                WalterSecretsManagerClient.POLYGON_API_KEY_SECRET_ID,
                WalterSecretsManagerClient.POLYGON_API_KEY_SECRET_NAME,
            )
        return self.polygon_api_key

    def get_jwt_secret_key(self) -> str:
        if self.jwt_secret_key is None:
            self.jwt_secret_key = self._get_secret(
                WalterSecretsManagerClient.JWT_SECRET_KEY_SECRET_ID,
                WalterSecretsManagerClient.JWT_SECRET_KEY_SECRET_NAME,
            )
        return self.jwt_secret_key

    def get_jwt_verify_email_secret_key(self) -> str:
        if self.jwt_verify_email_secret_key is None:
            self.jwt_verify_email_secret_key = self._get_secret(
                WalterSecretsManagerClient.JWT_VERIFY_EMAIL_SECRET_KEY_ID,
                WalterSecretsManagerClient.JWT_VERIFY_EMAIL_SECRET_KEY_NAME,
            )
        return self.jwt_verify_email_secret_key

    def _get_secret(self, secret_id: str, secret_name: str) -> str:
        return json.loads(
            self.client.get_secret_value(SecretId=secret_id)["SecretString"]
        )[secret_name]
