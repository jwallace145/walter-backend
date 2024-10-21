import json

import pytest

from src.api.get_stocks_for_user import GetStocksForUser
from src.api.models import Status, HTTPStatus
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from tst.api.utils import get_stocks_for_user_event


@pytest.fixture
def get_stocks_for_user_api(
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
    walter_sm: WalterSecretsManagerClient,
) -> GetStocksForUser:
    return GetStocksForUser(walter_cw, walter_db, walter_sm)


def test_get_stocks_for_user(
    get_stocks_for_user_api: GetStocksForUser, walter_db: WalterDB, jwt_walrus: str
) -> None:
    event = get_stocks_for_user_event(email="walrus@gmail.com", token=jwt_walrus)
    expected_response = get_expected_response(
        status_code=HTTPStatus.OK,
        status=Status.SUCCESS,
        message=[
            {
                "user_email": "walrus@gmail.com",
                "stock_symbol": "AMZN",
                "quantity": 100.0,
            },
            {
                "user_email": "walrus@gmail.com",
                "stock_symbol": "MSFT",
                "quantity": 100.0,
            },
            {
                "user_email": "walrus@gmail.com",
                "stock_symbol": "NFLX",
                "quantity": 100.0,
            },
        ],
    )
    assert expected_response == get_stocks_for_user_api.invoke(event)


def test_add_stock_failure_invalid_email(
    get_stocks_for_user_api: GetStocksForUser, jwt_walter: str
) -> None:
    event = get_stocks_for_user_event(email="walter", token=jwt_walter)
    expected_response = get_expected_response(
        status_code=HTTPStatus.OK, status=Status.FAILURE, message="Invalid email!"
    )
    assert expected_response == get_stocks_for_user_api.invoke(event)


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
                "API": "GetStocksForUser",
                "Status": status.value,
                "Message": message,
            }
        ),
    }
