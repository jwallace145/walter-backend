from src.auth.authenticator import WalterAuthenticator


def test_check_password(walter_authenticator: WalterAuthenticator) -> None:
    incorrect_password = "incorrect"
    password = "password"
    salt, hashed_password = walter_authenticator.hash_password(password)
    assert (
        walter_authenticator.check_password(password, hashed_password.decode()) is True
    )
    assert (
        walter_authenticator.check_password(
            incorrect_password, hashed_password.decode()
        )
        is False
    )


def test_validate_token(walter_authenticator: WalterAuthenticator) -> None:
    email = "walter@gmail.com"
    token = walter_authenticator.generate_token(email)
    decoded_token = walter_authenticator.decode_token(token)
    assert decoded_token["sub"] == "walter@gmail.com"
    assert walter_authenticator.decode_token("test-token") is None
