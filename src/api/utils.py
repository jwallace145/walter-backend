import re


def is_valid_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_valid_username(username: str) -> bool:
    return username.isalnum()


def get_token(event: dict) -> str:
    if event["headers"] is None or "Authorization" not in event["headers"]:
        return None
    return event["headers"]["Authorization"].split(" ")[1]
