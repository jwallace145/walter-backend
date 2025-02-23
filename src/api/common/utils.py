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


def is_valid_password(password: str) -> bool:
    """
    Validate password.

    Validates that the given password is at least eight characters long and
    includes at least three of the following types:

        1. Uppercase Letter
        2. Lowercase Letter
        3. Number
        4. Special Character

    This ensures that users utilize strong passwords that are not easily
    guessed or cracked.

    Args:
        password (str): The given password.

    Returns:
        (bool): True if the given password is valid; otherwise, False.
    """
    if len(password) < 8:
        return False

    count = 0
    if re.search(r"[A-Z]", password):
        count += 1

    if re.search(r"[a-z]", password):
        count += 1

    if re.search(r"[0-9]", password):
        count += 1

    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        count += 1

    if count < 3:
        return False

    return True
