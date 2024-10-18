import json

import pytest

from src.api.get_stocks_for_user import GetStocksForUser
from src.api.models import Status, HTTPStatus
from src.database.client import WalterDB
from tst.api.utils import get_stocks_for_user_event


@pytest.fixture
def get_stocks_for_user_api(walter_db: WalterDB) -> GetStocksForUser:
    return GetStocksForUser(walter_db)


def test_get_stocks_for_user(
    get_stocks_for_user_api: GetStocksForUser, walter_db: WalterDB
) -> None:
    event = get_stocks_for_user_event(email="walrus@gmail.com")
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
    get_stocks_for_user_api: GetStocksForUser,
) -> None:
    event = get_stocks_for_user_event(email="walter")
    expected_response = get_expected_response(
        status_code=HTTPStatus.OK, status=Status.FAILURE, message="Invalid email!"
    )
    assert expected_response == get_stocks_for_user_api.invoke(event)


def test_add_stock_failure_user_does_not_exist(
    get_stocks_for_user_api: GetStocksForUser,
) -> None:
    event = get_stocks_for_user_event(email="sally@gmail.com")
    expected_response = get_expected_response(
        status_code=HTTPStatus.OK, status=Status.FAILURE, message="User not found!"
    )
    assert expected_response == get_stocks_for_user_api.invoke(event)


def get_expected_response(
    status_code: HTTPStatus, status: Status, message: str
) -> dict:
    return {
        "statusCode": status_code.value,
        "body": json.dumps(
            {
                "API": "WalterAPI: GetStocksForUser",
                "Status": status.value,
                "Message": message,
            }
        ),
    }
