from src.aws.secretsmanager.client import WalterSecretsManagerClient


def test_get_access_token_secret_key(
    walter_sm: WalterSecretsManagerClient,
) -> None:
    assert walter_sm.get_access_token_secret_key() == "test-access-token-secret-key"


def test_get_refresh_token_secret_key(
    walter_sm: WalterSecretsManagerClient,
) -> None:
    assert walter_sm.get_refresh_token_secret_key() == "test-refresh-token-secret-key"


def test_get_polygon_api_key(
    walter_sm: WalterSecretsManagerClient,
) -> None:
    assert walter_sm.get_polygon_api_key() == "test-polygon-api-key"


def test_get_stripe_secret_key(
    walter_sm: WalterSecretsManagerClient,
) -> None:
    assert walter_sm.get_stripe_secret_key() == "test-stripe-secret-key"
