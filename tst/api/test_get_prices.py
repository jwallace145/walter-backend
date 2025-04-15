import pytest

from src.api.common.methods import Status, HTTPStatus
from src.api.get_prices import GetPrices
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.stocks.client import WalterStocksAPI
from tst.api.utils import get_get_prices_event, get_expected_response


@pytest.fixture
def get_prices_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
    walter_stocks_api: WalterStocksAPI,
    walter_sm: WalterSecretsManagerClient,
) -> GetPrices:
    return GetPrices(walter_authenticator, walter_cw, walter_db, walter_stocks_api)


def test_get_prices_success_exists_in_db(
    get_prices_api: GetPrices, walter_db: WalterDB
) -> None:
    event = get_get_prices_event(symbol="META", start_date="2025-01-01", end_date="2025-01-02")
    expected_response = get_expected_response(
        api_name=get_prices_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.SUCCESS,
        message="Retrieved prices!",
        data={
            "stock": "META",
            "start_date": "2025-01-01",
            "end_date": "2025-01-02",
            "num_prices": 3,
            "prices": [
                {
                    "symbol": "META",
                    "price": 200.0,
                    "timestamp": "2025-01-01T01:00:00",
                },
                {
                    "symbol": "META",
                    "price": 225.0,
                    "timestamp": "2025-01-01T02:00:00",
                },
                {
                    "symbol": "META",
                    "price": 250.0,
                    "timestamp": "2025-01-01T03:00:00",
                },
            ],
        },
    )
    assert walter_db.get_stock("META") is not None
    assert expected_response == get_prices_api.invoke(event)


def test_get_prices_success_does_not_exist_in_db(
    get_prices_api: GetPrices, walter_db: WalterDB
) -> None:
    event = get_get_prices_event(symbol="TEAM", start_date="2025-01-01", end_date="2025-01-02")
    expected_response = get_expected_response(
        api_name=get_prices_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.SUCCESS,
        message="Retrieved prices!",
        data={
            "stock": "TEAM",
            "start_date": "2025-01-01",
            "end_date": "2025-01-02",
            "num_prices": 3,
            "prices": [
                {
                    "symbol": "TEAM",
                    "price": 1.0,
                    "timestamp": "2025-01-01T01:00:00",
                },
                {
                    "symbol": "TEAM",
                    "price": 1.0,
                    "timestamp": "2025-01-01T02:00:00",
                },
                {
                    "symbol": "TEAM",
                    "price": 1.0,
                    "timestamp": "2025-01-01T03:00:00",
                },
            ],
        },
    )
    assert walter_db.get_stock("TEAM") is None
    assert expected_response == get_prices_api.invoke(event)
    assert walter_db.get_stock("TEAM") is not None


def test_get_prices_failure_stock_does_not_exist(
    get_prices_api: GetPrices,
    walter_db: WalterDB,
    walter_stocks_api: WalterStocksAPI,
) -> None:
    invalid_symbol = "INVALID"
    event = get_get_prices_event(symbol=invalid_symbol, start_date="2025-01-01", end_date="2025-01-02")
    expected_response = get_expected_response(
        api_name=get_prices_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Stock does not exist!",
    )
    assert walter_stocks_api.get_stock(invalid_symbol) is None
    assert walter_db.get_stock(invalid_symbol) is None
    assert expected_response == get_prices_api.invoke(event)
