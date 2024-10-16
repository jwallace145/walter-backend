import json

from src.api.create_user import CreateUser
from src.api.models import Status, HTTPStatus

AUTH_USER_EVENT = json.load(open("tst/api/data/event.json"))


def get_create_user_event(email: str, username: str, password: str) -> dict:
    AUTH_USER_EVENT["body"] = json.dumps(
        {"email": email, "username": username, "password": password}
    )
    return AUTH_USER_EVENT


def test_create_user(walter_db) -> None:
    event = get_create_user_event(email="jim@gmail.com", username="jim", password="jim")
    expected_response = get_expected_response(
        status_code=HTTPStatus.OK, status=Status.SUCCESS, message="User created!"
    )
    assert expected_response == CreateUser(walter_db).invoke(event)


def test_create_user_failure_user_already_exists(walter_db) -> None:
    event = get_create_user_event(
        email="walter@gmail.com", username="walter", password="walter"
    )
    expected_response = get_expected_response(
        status_code=HTTPStatus.OK, status=Status.FAILURE, message="User already exists!"
    )
    assert expected_response == CreateUser(walter_db).invoke(event)


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
