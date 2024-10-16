import json

EVENT = json.load(open("tst/api/data/event.json"))


def get_add_stock_event(email: str, stock: str, quantity: float) -> dict:
    EVENT["body"] = json.dumps({"email": email, "stock": stock, "quantity": quantity})
    return EVENT


def get_create_user_event(email: str, username: str, password: str) -> dict:
    EVENT["body"] = json.dumps(
        {"email": email, "username": username, "password": password}
    )
    return EVENT
