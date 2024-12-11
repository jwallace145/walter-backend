import re


def is_valid_email(email: str) -> bool:
    """
    Validate email address.

    Args:
        email: The email address to be validated.

    Returns:
        True if the given email address is valid; otherwise, False.
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def is_valid_username(username: str) -> bool:
    """
    Validate username.

    Validates a username only contains alphanumeric characters.

    Args:
        username: The given username.

    Returns:
        True if the given username is contains exclusively alphanumeric characters; otherwise, False.
    """
    return username.isalnum()
