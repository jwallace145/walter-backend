import json

import pytest

from src.api.add_stock import AddStock
from src.api.models import Status, HTTPStatus
from src.database.client import WalterDB
from tst.api.utils import get_add_stock_event


@pytest.fixture
def add_stock_api(walter_db: WalterDB) -> AddStock:
    return AddStock(walter_db)


def test_add_stock(add_stock_api: AddStock) -> None:
    event = get_add_stock_event(email="walter@gmail.com", stock="ABNB", quantity=100.0)
    expected_response = get_expected_response(
        status_code=HTTPStatus.OK, status=Status.SUCCESS, message="Stock added!"
    )
    assert expected_response == add_stock_api.invoke(event)


def test_add_stock_failure_invalid_email(add_stock_api: AddStock) -> None:
    event = get_add_stock_event(email="walter", stock="ABNB", quantity=100.0)
    expected_response = get_expected_response(
        status_code=HTTPStatus.OK, status=Status.FAILURE, message="Invalid email!"
    )
    assert expected_response == add_stock_api.invoke(event)


def test_add_stock_failure_user_does_not_exist(add_stock_api: AddStock) -> None:
    event = get_add_stock_event(email="sally@gmail.com", stock="ABNB", quantity=100.0)
    expected_response = get_expected_response(
        status_code=HTTPStatus.OK, status=Status.FAILURE, message="User not found!"
    )
    assert expected_response == add_stock_api.invoke(event)


def get_expected_response(
    status_code: HTTPStatus, status: Status, message: str
) -> dict:
    return {
        "statusCode": status_code.value,
        "body": json.dumps(
            {
                "API": "WalterAPI: AddStock",
                "Status": status.value,
                "Message": message,
            }
        ),
    }
