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
    email = "john@gmail.com"
    user_id = "user-004"
    account_id = "acct-006"

    # assert account exists prior to api invocation
    assert walter_db.get_account(user_id, account_id) is not None
    assert walter_db.get_transactions_by_account(account_id) is not None
    assert walter_db.get_holdings(account_id) is not None

    # prepare delete account event
    jwt = walter_authenticator.generate_user_token(email)
    create_delete_account_event(jwt, account_id)

    event = create_delete_account_event(jwt, account_id)
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
    delete_account_api: DeleteAccount, jwt_walter: str
) -> None:
    # omit account_id
    event = create_delete_account_event(jwt_walter, None)
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
    event = create_delete_account_event("invalid-token", "acct-123")
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
    event = create_delete_account_event(ghost_token, "acct-ghost")
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
    event = create_delete_account_event(jwt_walter, "does-not-exist")
    expected_response = get_expected_response(
        api_name=delete_account_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Account does not exist!",
    )
    assert expected_response == delete_account_api.invoke(event)
