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
        - JWTAccessTokenSecretKey: The JSON web token (JWT) secret key used to verify user identity.
        - JWTRefreshTokenSecretKey: The JSON web token (JWT) secret key used to verify user identity.
    """

    POLYGON_API_KEY_SECRET_ID = "PolygonAPIKey"
    POLYGON_API_KEY_SECRET_NAME = "POLYGON_API_KEY"
    ACCESS_TOKEN_SECRET_KEY_ID = "WalterAuthSecrets-dev"
    ACCESS_TOKEN_SECRET_KEY_NAME = "ACCESS_TOKEN_SECRET_KEY"
    REFRESH_TOKEN_SECRET_KEY_ID = "WalterAuthSecrets-dev"
    REFRESH_TOKEN_SECRET_KEY_NAME = "REFRESH_TOKEN_SECRET_KEY"
    STRIPE_TEST_SECRET_KEY_ID = "StripeTestSecretKey"
    STRIPE_TEST_SECRET_KEY_NAME = "STRIPE_TEST_SECRET_KEY"
    PLAID_SANDBOX_CREDENTIALS_SECRET_NAME = "PlaidSandboxCredentials"
    PLAID_SANDBOX_CREDENTIALS_CLIENT_ID_KEY = "PLAID_SANDBOX_CREDENTIALS_CLIENT_ID"
    PLAID_SANDBOX_CREDENTIALS_SECRET_KEY = "PLAID_SANDBOX_CREDENTIALS_SECRET"

    client: SecretsManagerClient
    domain: Domain

    # lazy init all secrets
    polygon_api_key: str = None
    access_token_secret_key: str = None
    refresh_token_secret_key: str = None
    stripe_test_secret_key: str = None
    plaid_sandbox_credentials_client_id: str = None
    plaid_sandbox_credentials_secret_key: str = None

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

    def get_access_token_secret_key(self) -> str:
        if self.access_token_secret_key is None:
            self.access_token_secret_key = self._get_secret(
                self.ACCESS_TOKEN_SECRET_KEY_ID,
                self.ACCESS_TOKEN_SECRET_KEY_NAME,
            )
        return self.access_token_secret_key

    def get_refresh_token_secret_key(self) -> str:
        if self.refresh_token_secret_key is None:
            self.refresh_token_secret_key = self._get_secret(
                self.REFRESH_TOKEN_SECRET_KEY_ID,
                self.REFRESH_TOKEN_SECRET_KEY_NAME,
            )
        return self.refresh_token_secret_key

    def get_stripe_test_secret_key(self) -> str:
        if self.stripe_test_secret_key is None:
            self.stripe_test_secret_key = self._get_secret(
                WalterSecretsManagerClient.STRIPE_TEST_SECRET_KEY_ID,
                WalterSecretsManagerClient.STRIPE_TEST_SECRET_KEY_NAME,
            )
        return self.stripe_test_secret_key

    def get_plaid_sandbox_credentials_client_id(self) -> str:
        if self.plaid_sandbox_credentials_client_id is None:
            self.plaid_sandbox_credentials_client_id = self._get_secret(
                WalterSecretsManagerClient.PLAID_SANDBOX_CREDENTIALS_SECRET_NAME,
                WalterSecretsManagerClient.PLAID_SANDBOX_CREDENTIALS_CLIENT_ID_KEY,
            )
        return self.plaid_sandbox_credentials_client_id

    def get_plaid_sandbox_credentials_secret_key(self) -> str:
        if self.plaid_sandbox_credentials_secret_key is None:
            self.plaid_sandbox_credentials_secret_key = self._get_secret(
                WalterSecretsManagerClient.PLAID_SANDBOX_CREDENTIALS_SECRET_NAME,
                WalterSecretsManagerClient.PLAID_SANDBOX_CREDENTIALS_SECRET_KEY,
            )
        return self.plaid_sandbox_credentials_secret_key

    def _get_secret(self, secret_id: str, secret_name: str) -> str:
        return json.loads(
            self.client.get_secret_value(SecretId=secret_id)["SecretString"]
        )[secret_name]
