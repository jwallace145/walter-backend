from src.utils.auth import hash_password, check_password, generate_token, validate_token
from tst.conftest import SECRETS_MANAGER_JWT_SECRET_KEY_SECRET_VALUE


def test_check_password() -> None:
    incorrect_password = "incorrect"
    password = "password"
    salt, hashed_password = hash_password(password)
    assert check_password(password, hashed_password.decode()) is True
    assert check_password(incorrect_password, hashed_password.decode()) is False


def test_validate_token() -> None:
    email = "walter@gmail.com"
    token = generate_token(email, SECRETS_MANAGER_JWT_SECRET_KEY_SECRET_VALUE)
    assert validate_token(token, SECRETS_MANAGER_JWT_SECRET_KEY_SECRET_VALUE) is True
    assert (
        validate_token("test-token", SECRETS_MANAGER_JWT_SECRET_KEY_SECRET_VALUE)
        is False
    )
