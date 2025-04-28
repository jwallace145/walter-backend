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


def is_valid_name(first_name: str, last_name: str) -> bool:
    """
    Validate name.

    This method validates user's names. Special characters that are still
    valid include accented characters, hyphens, and spaces.

    Args:
        first_name: The first name of the user.
        last_name: The last name of the user.

    Returns:
        True if the given name is valid; otherwise, False.
    """
    pattern = r"^[a-zA-ZÀ-ÖØ-öø-ÿ' -]+$"
    return bool(re.fullmatch(pattern, first_name.strip())) and bool(
        re.fullmatch(pattern, last_name.strip())
    )


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
