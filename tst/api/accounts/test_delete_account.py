import json

import pytest

from src.api.accounts.delete_account import DeleteAccount
from src.api.common.models import HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.database.client import WalterDB
from src.metrics.client import DatadogMetricsClient
from tst.api.utils import get_expected_response


@pytest.fixture
def delete_account_api(
    walter_authenticator: WalterAuthenticator,
    datadog_metrics: DatadogMetricsClient,
    walter_db: WalterDB,
) -> DeleteAccount:
    return DeleteAccount(walter_authenticator, datadog_metrics, walter_db)


def create_delete_account_event(token: str, account_id: str) -> dict:
    return {
        "path": "/accounts",
        "httpMethod": "DELETE",
        "headers": {
            "Authorization": f"Bearer {token}",
            "content-type": "application/json",
        },
        "queryStringParameters": None,
        "body": json.dumps(
            {
                "account_id": account_id,
            }
        ),
    }


def test_delete_account_success(
    delete_account_api: DeleteAccount,
    walter_db: WalterDB,
    walter_authenticator: WalterAuthenticator,
) -> None:
    # data seeded in the mock db
    user_id = "user-004"
    session_id = "session-003"
    account_id = "acct-006"

    # assert account exists prior to api invocation
    assert walter_db.get_account(user_id, account_id) is not None
    assert walter_db.get_transactions_by_account(account_id) is not None
    assert walter_db.get_holdings(account_id) is not None

    # prepare delete account event
    token, token_expiry = walter_authenticator.generate_access_token(
        user_id, session_id
    )
    event = create_delete_account_event(token, account_id)

    expected_response = get_expected_response(
        api_name=delete_account_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.SUCCESS,
        message="Successfully deleted account!",
    )

    # assert expected response
    assert expected_response == delete_account_api.invoke(event)

    # assert account, transactions, and holdings are deleted
    assert walter_db.get_account(user_id, account_id) is None
    assert walter_db.get_transactions_by_account(account_id) == []
    assert walter_db.get_holdings(account_id) == []


def test_delete_account_failure_missing_required_field(
    delete_account_api: DeleteAccount, walter_authenticator: WalterAuthenticator
) -> None:
    user_id = "user-001"
    session_id = "session-001"
    account_id = None  # omit account_id
    token, token_expiry = walter_authenticator.generate_access_token(
        user_id, session_id
    )
    event = create_delete_account_event(token, account_id)
    expected_response = get_expected_response(
        api_name=delete_account_api.API_NAME,
        status_code=HTTPStatus.BAD_REQUEST,
        status=Status.SUCCESS,
        message="Client bad request! Missing required field: 'account_id'",
    )
    assert expected_response == delete_account_api.invoke(event)


def test_delete_account_failure_not_authenticated(
    delete_account_api: DeleteAccount,
) -> None:
    event = create_delete_account_event("invalid-token", "acct-123")
    expected_response = get_expected_response(
        api_name=delete_account_api.API_NAME,
        status_code=HTTPStatus.UNAUTHORIZED,
        status=Status.SUCCESS,
        message="Not authenticated! Token is expired or invalid.",
    )
    assert expected_response == delete_account_api.invoke(event)


def test_delete_account_failure_session_does_not_exist(
    delete_account_api: DeleteAccount, walter_authenticator: WalterAuthenticator
) -> None:
    user_id = "user-001"
    session_id = "session-does-not-exist"
    token, token_expiry = walter_authenticator.generate_access_token(
        user_id, session_id
    )
    event = create_delete_account_event(token, "acct-ghost")
    expected_response = get_expected_response(
        api_name=delete_account_api.API_NAME,
        status_code=HTTPStatus.UNAUTHORIZED,
        status=Status.SUCCESS,
        message="Not authenticated! Session does not exist.",
    )
    assert expected_response == delete_account_api.invoke(event)


def test_delete_account_failure_account_does_not_exist(
    delete_account_api: DeleteAccount, walter_authenticator: WalterAuthenticator
) -> None:
    user_id = "user-001"
    session_id = "session-001"
    account_id = "acct-does-not-exist"
    token, token_expiry = walter_authenticator.generate_access_token(
        user_id, session_id
    )
    event = create_delete_account_event(token, account_id)
    expected_response = get_expected_response(
        api_name=delete_account_api.API_NAME,
        status_code=HTTPStatus.NOT_FOUND,
        status=Status.SUCCESS,
        message="Account does not exist!",
    )
    assert expected_response == delete_account_api.invoke(event)
