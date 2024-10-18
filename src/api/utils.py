import json
import re

from src.api.exceptions import NotAuthenticated
from src.utils.auth import decode_token


def is_valid_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_valid_username(username: str) -> bool:
    return username.isalnum()


def authenticate_request(event: dict, key: str) -> bool:
    token = get_token(event)
    if token is None:
        raise NotAuthenticated("Not authenticated!")

    decoded_token = decode_token(token, key)
    if decoded_token is None:
        raise NotAuthenticated("Not authenticated!")

    body = json.loads(event["body"])
    email = body["email"]

    authenticated_user = decoded_token["sub"]
    if email != authenticated_user:
        raise NotAuthenticated("Not authenticated!")


def get_token(event: dict) -> str:
    if event["headers"] is None or "Authorization" not in event["headers"]:
        return None
    return event["headers"]["Authorization"].split(" ")[1]
