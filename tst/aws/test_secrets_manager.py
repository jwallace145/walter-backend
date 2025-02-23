from src.aws.secretsmanager.client import WalterSecretsManagerClient


def test_get_alpha_vantage_api_key(walter_sm: WalterSecretsManagerClient) -> None:
    assert walter_sm.get_alpha_vantage_api_key() == "test-alpha-vantage-api-key"


def test_get_polygon_api_key(
    walter_sm: WalterSecretsManagerClient,
) -> None:
    assert walter_sm.get_polygon_api_key() == "test-polygon-api-key"


def test_get_stock_news_api_key(
    walter_sm: WalterSecretsManagerClient,
) -> None:
    assert walter_sm.get_stock_news_api_key() == "test-stock-news-api-key"


def test_get_jwt_secret_key(
    walter_sm: WalterSecretsManagerClient,
) -> None:
    assert walter_sm.get_jwt_secret_key() == "test-jwt-secret-key"


def test_get_jwt_change_password_secret_key(
    walter_sm: WalterSecretsManagerClient,
) -> None:
    assert walter_sm.get_jwt_change_password_secret_key() == "test-change-password-key"


def test_get_jwt_verify_email_secret_key(
    walter_sm: WalterSecretsManagerClient,
) -> None:
    assert walter_sm.get_jwt_verify_email_secret_key() == "test-verify-email-key"
