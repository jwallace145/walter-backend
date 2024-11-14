import pytest

from src.api.get_portfolio import GetPortfolio
from src.api.methods import Status, HTTPStatus
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.stocks.client import WalterStocksAPI
from tst.api.utils import get_portfolio_event, get_expected_response


@pytest.fixture
def get_portfolio_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
    walter_sm: WalterSecretsManagerClient,
    walter_stocks_api: WalterStocksAPI,
) -> GetPortfolio:
    return GetPortfolio(
        walter_authenticator, walter_cw, walter_db, walter_sm, walter_stocks_api
    )


def test_get_portfolio(
    get_portfolio_api: GetPortfolio,
    walter_db: WalterDB,
    walter_authenticator: WalterAuthenticator,
) -> None:
    event = get_portfolio_event(
        token=walter_authenticator.generate_token("walrus@gmail.com")
    )
    expected_response = get_expected_response(
        api_name=get_portfolio_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.SUCCESS,
        message="Retrieved portfolio!",
        data={
            "total_equity": 35_000.0,
            "stocks": [
                {
                    "symbol": "AAPL",
                    "company": "Apple",
                    "price": 100.0,
                    "quantity": 100.0,
                    "equity": 10_000.0,
                },
                {
                    "symbol": "META",
                    "company": "Meta",
                    "price": 250.0,
                    "quantity": 100.0,
                    "equity": 25_000.0,
                },
            ],
        },
    )
    assert expected_response == get_portfolio_api.invoke(event)
