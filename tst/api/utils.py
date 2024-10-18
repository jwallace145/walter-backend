import json

EVENT = json.load(open("tst/api/data/event.json"))


def get_auth_user_event(email: str, password: str) -> dict:
    EVENT["body"] = json.dumps({"email": email, "password": password})
    return EVENT


def get_add_stock_event(email: str, stock: str, quantity: float, token: str) -> dict:
    EVENT["body"] = json.dumps({"email": email, "stock": stock, "quantity": quantity})
    EVENT["headers"] = {"Authorization": f"Bearer {token}"}
    return EVENT


def get_stocks_for_user_event(email: str, token: str) -> dict:
    EVENT["body"] = json.dumps({"email": email})
    EVENT["headers"] = {"Authorization": f"Bearer {token}"}
    return EVENT


def get_create_user_event(email: str, username: str, password: str) -> dict:
    EVENT["body"] = json.dumps(
        {"email": email, "username": username, "password": password}
    )
    return EVENT


def get_send_newsletter_event(email: str, token: str) -> dict:
    EVENT["body"] = json.dumps({"email": email})
    EVENT["headers"] = {"Authorization": f"Bearer {token}"}
    return EVENT
