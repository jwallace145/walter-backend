from src.auth.authenticator import WalterAuthenticator


def test_check_password(walter_authenticator: WalterAuthenticator) -> None:
    incorrect_password = "incorrect"
    password = "password"
    salt, hashed_password = walter_authenticator.hash_secret(password)
    assert walter_authenticator.check_secret(password, hashed_password.decode()) is True
    assert (
        walter_authenticator.check_secret(incorrect_password, hashed_password.decode())
        is False
    )


def test_validate_access_tokens_success(
    walter_authenticator: WalterAuthenticator,
) -> None:
    user_id = "user-001"
    session_id = "session-001"
    token, token_expiry = walter_authenticator.generate_access_token(
        user_id, session_id
    )
    decoded_user_id, decoded_jti = walter_authenticator.decode_access_token(token)
    assert decoded_user_id == user_id
    assert decoded_jti == session_id
    assert walter_authenticator.decode_access_token("test-token") is None
