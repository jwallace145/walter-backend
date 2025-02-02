import json

from src.api.common.methods import HTTPStatus, Status

###############
# TEST EVENTS #
###############

EVENT = json.load(open("tst/api/data/event.json"))


def get_auth_user_event(email: str, password: str) -> dict:
    EVENT["body"] = json.dumps({"email": email, "password": password})
    return EVENT


def get_get_stock_event(symbol: str) -> dict:
    EVENT["queryStringParameters"] = {"symbol": symbol}
    return EVENT


def get_add_stock_event(stock: str, quantity: float, token: str) -> dict:
    EVENT["body"] = json.dumps({"stock": stock, "quantity": quantity})
    EVENT["headers"] = {
        "Authorization": f"Bearer {token}",
        "content-type": "application/json",
    }
    return EVENT


def get_delete_stock_event(stock: str, token: str) -> dict:
    EVENT["body"] = json.dumps({"stock": stock})
    EVENT["headers"] = {
        "Authorization": f"Bearer {token}",
        "content-type": "application/json",
    }
    return EVENT


def get_get_prices_event(symbol: str) -> dict:
    EVENT["body"] = json.dumps({"stock": symbol})
    EVENT["headers"] = {"content-type": "application/json"}
    return EVENT


def get_portfolio_event(token: str) -> dict:
    EVENT["headers"] = {"Authorization": f"Bearer {token}"}
    return EVENT


def get_news_summary_event(stock: str) -> dict:
    EVENT["body"] = json.dumps({"stock": stock})
    EVENT["headers"] = {"content-type": "application/json"}
    return EVENT


def get_create_user_event(email: str, username: str, password: str) -> dict:
    EVENT["body"] = json.dumps(
        {"email": email, "username": username, "password": password}
    )
    EVENT["headers"] = {"content-type": "application/json"}
    return EVENT


def get_get_user_event(token: str) -> dict:
    EVENT["headers"] = {"Authorization": f"Bearer {token}"}
    return EVENT


def get_send_newsletter_event(token: str) -> dict:
    EVENT["headers"] = {"Authorization": f"Bearer {token}"}
    return EVENT


def get_verify_email_event(email_token: str) -> dict:
    EVENT["headers"] = {"Authorization": f"Bearer {email_token}"}
    return EVENT


def get_send_verify_email_event(token: str) -> dict:
    EVENT["headers"] = {"Authorization": f"Bearer {token}"}
    return EVENT


def get_change_password_event(token: str, new_password: str) -> dict:
    EVENT["headers"] = {
        "Authorization": f"Bearer {token}",
        "content-type": "application/json",
    }
    EVENT["body"] = json.dumps({"new_password": new_password})
    return EVENT


def get_send_change_password_email_event(email: str) -> dict:
    EVENT["queryStringParameters"] = {"email": email}
    return EVENT


def get_subscribe_event(token: str) -> dict:
    EVENT["headers"] = {"Authorization": f"Bearer {token}"}
    return EVENT


def get_unsubscribe_event(token: str) -> dict:
    EVENT["headers"] = {"Authorization": f"Bearer {token}"}
    return EVENT


def get_search_stocks_event(stock: str) -> dict:
    EVENT["queryStringParameters"] = {"symbol": stock}
    return EVENT


#####################
# EXPECTED RESPONSE #
#####################


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
            "Access-Control-Allow-Methods": "GET,OPTIONS,POST,DELETE",
        },
        "body": json.dumps(body),
    }
