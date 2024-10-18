import json

import pytest

from src.api.create_user import CreateUser
from src.api.models import Status, HTTPStatus
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from tst.api.utils import get_create_user_event


@pytest.fixture
def create_user_api(
    walter_db: WalterDB, walter_sm: WalterSecretsManagerClient
) -> CreateUser:
    return CreateUser(walter_db, walter_sm)


def test_create_user(create_user_api: CreateUser) -> None:
    event = get_create_user_event(email="jim@gmail.com", username="jim", password="jim")
    expected_response = get_expected_response(
        status_code=HTTPStatus.OK, status=Status.SUCCESS, message="User created!"
    )
    assert expected_response == create_user_api.invoke(event)


def test_create_user_failure_invalid_email(create_user_api: CreateUser) -> None:
    event = get_create_user_event(email="jim", username="jim", password="jim")
    expected_response = get_expected_response(
        status_code=HTTPStatus.OK, status=Status.FAILURE, message="Invalid email!"
    )
    assert expected_response == create_user_api.invoke(event)


def test_create_user_failure_invalid_username(create_user_api: CreateUser) -> None:
    event = get_create_user_event(
        email="jim@gmail.com", username="jim ", password="jim"
    )
    expected_response = get_expected_response(
        status_code=HTTPStatus.OK, status=Status.FAILURE, message="Invalid username!"
    )
    assert expected_response == create_user_api.invoke(event)


def test_create_user_failure_user_already_exists(create_user_api: CreateUser) -> None:
    event = get_create_user_event(
        email="walter@gmail.com", username="walter", password="walter"
    )
    expected_response = get_expected_response(
        status_code=HTTPStatus.OK, status=Status.FAILURE, message="User already exists!"
    )
    assert expected_response == create_user_api.invoke(event)


def get_expected_response(
    status_code: HTTPStatus, status: Status, message: str
) -> dict:
    return {
        "statusCode": status_code.value,
        "body": json.dumps(
            {
                "API": "WalterAPI: CreateUser",
                "Status": status.value,
                "Message": message,
            }
        ),
    }
