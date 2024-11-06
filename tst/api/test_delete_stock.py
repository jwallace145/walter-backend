import pytest

from src.api.delete_stock import DeleteStock
from src.api.methods import HTTPStatus, Status
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.users.models import User
from src.stocks.client import WalterStocksAPI
from src.database.client import WalterDB
from tst.api.utils import get_expected_response, get_delete_stock_event

WALTER = User(email="walter@gmail.com", username="walter", password_hash="walter")


@pytest.fixture
def delete_stock_api(
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
    walter_stocks_api: WalterStocksAPI,
    walter_sm: WalterSecretsManagerClient,
) -> DeleteStock:
    return DeleteStock(walter_cw, walter_db, walter_stocks_api, walter_sm)


def test_delete_stock(
    delete_stock_api: DeleteStock, jwt_walter: str, walter_db: WalterDB
) -> None:
    stocks = walter_db.get_stocks_for_user(WALTER)
    assert "AAPL" in set(stocks.keys())

    event = get_delete_stock_event(stock="AAPL", token=jwt_walter)
    expected_response = get_expected_response(
        api_name=delete_stock_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.SUCCESS,
        message="Stock deleted!",
    )
    actual_response = delete_stock_api.invoke(event)

    stocks = walter_db.get_stocks_for_user(WALTER)
    assert "AAPL" not in set(stocks.keys())

    assert expected_response == actual_response
