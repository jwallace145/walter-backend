from src.utils.auth import hash_password, check_password


def test_check_password() -> None:
    incorrect_password = "incorrect"
    password = "password"
    salt, hashed_password = hash_password(password)
    assert check_password(password, hashed_password.decode()) is True
    assert check_password(incorrect_password, hashed_password.decode()) is False
