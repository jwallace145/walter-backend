import json

import pytest

from src.api.get_portfolio import GetPortfolio
from src.api.models import Status, HTTPStatus
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.stocks.client import WalterStocksAPI
from tst.api.utils import get_portfolio_event


@pytest.fixture
def get_portfolio_api(
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
    walter_sm: WalterSecretsManagerClient,
    walter_stocks_api: WalterStocksAPI,
) -> GetPortfolio:
    return GetPortfolio(walter_cw, walter_db, walter_sm, walter_stocks_api)


def test_get_stocks_for_user(
    get_portfolio_api: GetPortfolio, walter_db: WalterDB, jwt_walrus: str
) -> None:
    event = get_portfolio_event(email="walrus@gmail.com", token=jwt_walrus)
    expected_response = get_expected_response(
        status_code=HTTPStatus.OK,
        status=Status.SUCCESS,
        message=[
            {"symbol": "AAPL", "price": 100.0, "quantity": 100.0, "equity": 10000.0},
            {"symbol": "META", "price": 250.0, "quantity": 100.0, "equity": 25000.0},
        ],
    )
    assert expected_response == get_portfolio_api.invoke(event)


def test_add_stock_failure_invalid_email(
    get_portfolio_api: GetPortfolio, jwt_walter: str
) -> None:
    event = get_portfolio_event(email="walter", token=jwt_walter)
    expected_response = get_expected_response(
        status_code=HTTPStatus.OK, status=Status.FAILURE, message="Invalid email!"
    )
    assert expected_response == get_portfolio_api.invoke(event)


def get_expected_response(
    status_code: HTTPStatus, status: Status, message: str
) -> dict:
    return {
        "statusCode": status_code.value,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,OPTIONS,POST",
        },
        "body": json.dumps(
            {
                "API": "GetPortfolio",
                "Status": status.value,
                "Message": message,
            }
        ),
    }
