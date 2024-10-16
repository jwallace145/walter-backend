import pytest

from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.environment import Domain
from tst.conftest import (
    SECRETS_MANAGER_POLYGON_API_KEY_VALUE,
    SECRETS_MANAGER_JWT_SECRET_KEY_SECRET_VALUE,
)


@pytest.fixture
def walter_secrets_manager_client(
    secrets_manager_client,
) -> WalterSecretsManagerClient:
    return WalterSecretsManagerClient(secrets_manager_client, Domain.TESTING)


def test_get_polygon_api_key(
    walter_secrets_manager_client: WalterSecretsManagerClient,
) -> None:
    assert (
        walter_secrets_manager_client.get_polygon_api_key()
        == SECRETS_MANAGER_POLYGON_API_KEY_VALUE
    )


def test_get_jwt_secret_key(
    walter_secrets_manager_client: WalterSecretsManagerClient,
) -> None:
    assert (
        walter_secrets_manager_client.get_jwt_secret_key()
        == SECRETS_MANAGER_JWT_SECRET_KEY_SECRET_VALUE
    )
