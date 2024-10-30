import json

from src.api.models import HTTPStatus, Status

EVENT = json.load(open("tst/api/data/event.json"))


def get_auth_user_event(email: str, password: str) -> dict:
    EVENT["body"] = json.dumps({"email": email, "password": password})
    return EVENT


def get_add_stock_event(email: str, stock: str, quantity: float, token: str) -> dict:
    EVENT["body"] = json.dumps({"email": email, "stock": stock, "quantity": quantity})
    EVENT["headers"] = {"Authorization": f"Bearer {token}"}
    return EVENT


def get_portfolio_event(email: str, token: str) -> dict:
    EVENT["body"] = json.dumps({"email": email})
    EVENT["headers"] = {"Authorization": f"Bearer {token}"}
    return EVENT


def get_create_user_event(email: str, username: str, password: str) -> dict:
    EVENT["body"] = json.dumps(
        {"email": email, "username": username, "password": password}
    )
    return EVENT


def get_get_user_event(token: str) -> dict:
    EVENT["headers"] = {"Authorization": f"Bearer {token}"}
    return EVENT


def get_send_newsletter_event(email: str, token: str) -> dict:
    EVENT["body"] = json.dumps({"email": email})
    EVENT["headers"] = {"Authorization": f"Bearer {token}"}
    return EVENT


def get_expected_response(
    api_name: str,
    status_code: HTTPStatus,
    status: Status,
    message: str,
    data: str = None,
) -> dict:
    body = {
        "API": api_name,
        "Status": status.value,
        "Message": message,
    }

    if data is not None:
        body["Data"] = data

    return {
        "statusCode": status_code.value,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,OPTIONS,POST",
        },
        "body": json.dumps(body),
    }
