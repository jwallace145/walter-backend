import json
import pytest

from src.api.accounts.delete_account import DeleteAccount
from src.api.common.models import HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from tst.api.utils import get_expected_response


@pytest.fixture
def delete_account_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
) -> DeleteAccount:
    return DeleteAccount(walter_authenticator, walter_cw, walter_db)


def _event_with_auth_and_body(token: str, body: dict) -> dict:
    return {
        "headers": {
            "Authorization": f"Bearer {token}",
            "content-type": "application/json",
        },
        "queryStringParameters": None,
        "body": json.dumps(body) if body is not None else None,
    }


def test_delete_account_success(
    delete_account_api: DeleteAccount, walter_db: WalterDB, jwt_walter: str
) -> None:
    user = walter_db.get_user_by_email("walter@gmail.com")
    existing = walter_db.get_accounts(user.user_id)
    assert len(existing) >= 1
    account_id = existing[0].account_id

    event = _event_with_auth_and_body(jwt_walter, {"account_id": account_id})
    expected_response = get_expected_response(
        api_name=delete_account_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.SUCCESS,
        message="Successfully deleted account!",
    )

    assert expected_response == delete_account_api.invoke(event)
    # verify account deleted
    assert walter_db.get_account(user.user_id, account_id) is None


def test_delete_account_failure_missing_required_field(
    delete_account_api: DeleteAccount, jwt_walter: str
) -> None:
    # omit account_id
    event = _event_with_auth_and_body(jwt_walter, {})
    expected_response = get_expected_response(
        api_name=delete_account_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Client bad request! Missing required field: 'account_id'",
    )
    assert expected_response == delete_account_api.invoke(event)


def test_delete_account_failure_not_authenticated(
    delete_account_api: DeleteAccount,
) -> None:
    event = _event_with_auth_and_body("invalid-token", {"account_id": "acct-123"})
    expected_response = get_expected_response(
        api_name=delete_account_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Not authenticated! Token is invalid.",
    )
    assert expected_response == delete_account_api.invoke(event)


def test_delete_account_failure_user_does_not_exist(
    delete_account_api: DeleteAccount, walter_authenticator: WalterAuthenticator
) -> None:
    ghost_token = walter_authenticator.generate_user_token("ghost@ghost.com")
    event = _event_with_auth_and_body(ghost_token, {"account_id": "acct-ghost"})
    expected_response = get_expected_response(
        api_name=delete_account_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="User with email 'ghost@ghost.com' does not exist!",
    )
    assert expected_response == delete_account_api.invoke(event)


def test_delete_account_failure_account_does_not_exist(
    delete_account_api: DeleteAccount, jwt_walter: str
) -> None:
    event = _event_with_auth_and_body(jwt_walter, {"account_id": "does-not-exist"})
    expected_response = get_expected_response(
        api_name=delete_account_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Account does not exist!",
    )
    assert expected_response == delete_account_api.invoke(event)
