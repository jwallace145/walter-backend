import pytest

from src.api.add_stock import AddStock
from src.api.common.methods import Status, HTTPStatus
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.stocks.client import WalterStocksAPI
from tst.api.utils import get_add_stock_event, get_expected_response


@pytest.fixture
def add_stock_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
    walter_stocks_api: WalterStocksAPI,
    walter_sm: WalterSecretsManagerClient,
) -> AddStock:
    return AddStock(
        walter_authenticator, walter_cw, walter_db, walter_stocks_api, walter_sm
    )


def test_add_stock(add_stock_api: AddStock, jwt_walter: str) -> None:
    event = get_add_stock_event(stock="ABNB", quantity=100.0, token=jwt_walter)
    expected_response = get_expected_response(
        api_name=add_stock_api.API_NAME,
        status_code=HTTPStatus.CREATED,
        status=Status.SUCCESS,
        message="Stock added!",
    )
    assert expected_response == add_stock_api.invoke(event)


def test_add_stock_failure_stock_does_not_exist(
    add_stock_api: AddStock, jwt_walter: str
) -> None:
    event = get_add_stock_event(stock="INVALID", quantity=100.0, token=jwt_walter)
    expected_response = get_expected_response(
        api_name=add_stock_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Stock does not exist!",
    )
    assert expected_response == add_stock_api.invoke(event)


def test_add_stock_failure_maximum_number_of_stocks(
    add_stock_api: AddStock, jwt_john: str
) -> None:
    event = get_add_stock_event(stock="META", quantity=1.0, token=jwt_john)
    expected_response = get_expected_response(
        api_name=add_stock_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Max number of stocks!",
    )
    assert expected_response == add_stock_api.invoke(event)


def test_add_stock_failure_quantity_not_a_number(
    add_stock_api: AddStock, jwt_john: str
) -> None:
    event = get_add_stock_event(stock="META", quantity="INVALID", token=jwt_john)
    expected_response = get_expected_response(
        api_name=add_stock_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Quantity must be a number!",
    )
    assert expected_response == add_stock_api.invoke(event)


def test_add_stock_failure_negative_quantity(
    add_stock_api: AddStock, jwt_john: str
) -> None:
    event = get_add_stock_event(stock="META", quantity=-1.2, token=jwt_john)
    expected_response = get_expected_response(
        api_name=add_stock_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Quantity must be a positive number!",
    )
    assert expected_response == add_stock_api.invoke(event)


def test_add_stock_failure_zero_quantity(
    add_stock_api: AddStock, jwt_john: str
) -> None:
    event = get_add_stock_event(stock="META", quantity=0, token=jwt_john)
    expected_response = get_expected_response(
        api_name=add_stock_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Quantity must be a positive number!",
    )
    assert expected_response == add_stock_api.invoke(event)
