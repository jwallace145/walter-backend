import json
from dataclasses import dataclass
from enum import Enum

from mypy_boto3_secretsmanager import SecretsManagerClient

from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass(frozen=True, kw_only=True)
class SecretConfig:
    """
    The AWS Secrets Manager secret configurations.

    This config stores the secret's name and key used to access the secret
    stored within AWS Secrets Manager. All secrets used by WalterBackend are
    stored as JSON objects hence the secret key is required in addition to
    the secret name.
    """

    secret_name: str
    secret_key: str


class Secrets(Enum):
    """
    WalterBackend Secrets

    This enum includes all the secrets required by WalterBackend for all components
    served by the application. Each secret is stored as a SecretConfig object which
    can be used to retrieve the secret's details to access the secret value from
    AWS Secrets Manager. These secrets are also modeled in the Terraform IaC and
    should remain up to date with the most current configurations.
    """

    ACCESS_TOKEN_SECRET_KEY = SecretConfig(
        secret_name="WalterBackend-Auth-Secrets", secret_key="ACCESS_TOKEN_SECRET_KEY"
    )
    REFRESH_TOKEN_SECRET_KEY = SecretConfig(
        secret_name="WalterBackend-Auth-Secrets", secret_key="REFRESH_TOKEN_SECRET_KEY"
    )
    PLAID_CLIENT_ID = SecretConfig(
        secret_name="WalterBackend-Plaid-Secrets", secret_key="PLAID_CLIENT_ID"
    )
    PLAID_SECRET_KEY = SecretConfig(
        secret_name="WalterBackend-Plaid-Secrets", secret_key="PLAID_SECRET_KEY"
    )
    POLYGON_API_KEY = SecretConfig(
        secret_name="WalterBackend-Polygon-Secrets", secret_key="POLYGON_API_KEY"
    )
    DATADOG_API_KEY = SecretConfig(
        secret_name="WalterBackend-Datadog-Secrets", secret_key="DATADOG_API_KEY"
    )
    DATADOG_APP_KEY = SecretConfig(
        secret_name="WalterBackend-Datadog-Secrets", secret_key="DATADOG_APP_KEY"
    )
    DATADOG_API_URL = SecretConfig(
        secret_name="WalterBackend-Datadog-Secrets", secret_key="DATADOG_API_URL"
    )
    STRIPE_SECRET_KEY = SecretConfig(
        secret_name="WalterBackend-Stripe-Secrets", secret_key="STRIPE_SECRET_KEY"
    )

    def get_secret_name(self, domain: Domain) -> str:
        return self.value.secret_name + f"-{domain.value}"

    def get_secret_key(self) -> str:
        return self.value.secret_key

    @classmethod
    def from_string(cls, secret_name: str):
        for secret_enum in cls:
            if secret_enum.name.lower() == secret_name:
                return secret_enum
        raise ValueError(f"Invalid secret name: {secret_name}")


@dataclass
class WalterSecretsManagerClient:
    """
    WalterSecretsManagerClient

    This client is responsible for retrieving secrets from AWS Secrets Manager used for
    generating/decoding authentication tokens and calling external APIs. All secrets are
    lazily-loaded and pulled from AWS Secrets Manager on the component's first use. This
    ensures that access can be restricted to the set of secrets that the current component
    requires.

    See the Secrets enum for a list of all secrets used by WalterBackend.
    """

    client: SecretsManagerClient
    domain: Domain

    # lazy init all secrets
    access_token_secret_key: str = None
    refresh_token_secret_key: str = None
    plaid_sandbox_credentials_client_id: str = None
    plaid_sandbox_credentials_secret_key: str = None
    polygon_api_key: str = None
    datadog_api_key: str = None
    stripe_test_secret_key: str = None

    def __post_init__(self) -> None:
        log.debug(
            f"Creating {self.domain.value} SecretsManager client in region '{self.client.meta.region_name}'"
        )

    def get_polygon_api_key(self) -> str:
        if self.polygon_api_key is None:
            self.polygon_api_key = self._get_secret(
                Secrets.POLYGON_API_KEY.get_secret_name(self.domain),
                Secrets.POLYGON_API_KEY.get_secret_key(),
            )
        return self.polygon_api_key

    def get_access_token_secret_key(self) -> str:
        if self.access_token_secret_key is None:
            self.access_token_secret_key = self._get_secret(
                Secrets.ACCESS_TOKEN_SECRET_KEY.get_secret_name(self.domain),
                Secrets.ACCESS_TOKEN_SECRET_KEY.get_secret_key(),
            )
        return self.access_token_secret_key

    def get_refresh_token_secret_key(self) -> str:
        if self.refresh_token_secret_key is None:
            self.refresh_token_secret_key = self._get_secret(
                Secrets.REFRESH_TOKEN_SECRET_KEY.get_secret_name(self.domain),
                Secrets.REFRESH_TOKEN_SECRET_KEY.get_secret_key(),
            )
        return self.refresh_token_secret_key

    def get_stripe_secret_key(self) -> str:
        if self.stripe_test_secret_key is None:
            self.stripe_test_secret_key = self._get_secret(
                Secrets.STRIPE_SECRET_KEY.get_secret_name(self.domain),
                Secrets.STRIPE_SECRET_KEY.get_secret_key(),
            )
        return self.stripe_test_secret_key

    def get_plaid_client_id(self) -> str:
        if self.plaid_sandbox_credentials_client_id is None:
            self.plaid_sandbox_credentials_client_id = self._get_secret(
                Secrets.PLAID_CLIENT_ID.get_secret_name(self.domain),
                Secrets.PLAID_CLIENT_ID.get_secret_key(),
            )
        return self.plaid_sandbox_credentials_client_id

    def get_plaid_secret_key(self) -> str:
        if self.plaid_sandbox_credentials_secret_key is None:
            self.plaid_sandbox_credentials_secret_key = self._get_secret(
                Secrets.PLAID_SECRET_KEY.get_secret_name(self.domain),
                Secrets.PLAID_SECRET_KEY.get_secret_key(),
            )
        return self.plaid_sandbox_credentials_secret_key

    def get_datadog_api_key(self) -> str:
        if self.datadog_api_key is None:
            self.datadog_api_key = self._get_secret(
                Secrets.DATADOG_API_KEY.get_secret_name(self.domain),
                Secrets.DATADOG_API_KEY.get_secret_key(),
            )
        return self.datadog_api_key

    def _get_secret(self, secret_id: str, secret_name: str) -> str:
        return json.loads(
            self.client.get_secret_value(SecretId=secret_id)["SecretString"]
        )[secret_name]
