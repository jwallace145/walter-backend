import pytest

from src.api.accounts.get_accounts import GetAccounts
from src.api.common.models import HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from tst.api.utils import get_expected_response
from freezegun import freeze_time


@pytest.fixture
def get_accounts_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
) -> GetAccounts:
    return GetAccounts(walter_authenticator, walter_cw, walter_db)


def create_get_accounts_event(token: str) -> dict:
    return {
        "headers": {"Authorization": f"Bearer {token}"},
        "queryStringParameters": None,
        "path": "/accounts",
        "httpMethod": "GET",
        "body": None,
    }


@freeze_time("2025-07-01")
def test_get_accounts_success(
    get_accounts_api: GetAccounts,
    walter_db: WalterDB,
    walter_authenticator: WalterAuthenticator,
) -> None:
    # prepare event
    email = "walter@gmail.com"
    jwt = walter_authenticator.generate_user_token(email)
    event = create_get_accounts_event(jwt)

    # expected data from DB
    user = walter_db.get_user_by_email(email)
    accounts = walter_db.get_accounts(user.user_id)
    expected_data = {
        "total_num_accounts": len(accounts),
        "total_balance": sum([a.balance for a in accounts]),
        "accounts": [a.to_dict() for a in accounts],
    }

    expected_response = get_expected_response(
        api_name=get_accounts_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.SUCCESS,
        message="Successfully retrieved accounts!",
        data=expected_data,
    )

    assert expected_response == get_accounts_api.invoke(event)


@freeze_time("2025-07-01")
def test_get_accounts_failure_not_authenticated(
    get_accounts_api: GetAccounts,
) -> None:
    event = create_get_accounts_event("invalid-token")
    expected_response = get_expected_response(
        api_name=get_accounts_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Not authenticated! Token is invalid.",
    )
    assert expected_response == get_accounts_api.invoke(event)


@freeze_time("2025-07-01")
def test_get_accounts_failure_user_does_not_exist(
    get_accounts_api: GetAccounts, walter_authenticator: WalterAuthenticator
) -> None:
    # create a valid JWT for a non-existent user
    ghost_token = walter_authenticator.generate_user_token("ghost@ghost.com")
    event = create_get_accounts_event(ghost_token)
    expected_response = get_expected_response(
        api_name=get_accounts_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="User with email 'ghost@ghost.com' does not exist!",
    )
    assert expected_response == get_accounts_api.invoke(event)


@freeze_time("2025-07-01")
def test_get_accounts_success_update_balances(
    get_accounts_api: GetAccounts,
    walter_db: WalterDB,
    walter_authenticator: WalterAuthenticator,
) -> None:
    email = "bob@gmail.com"
    jwt = walter_authenticator.generate_user_token(email)
    event = create_get_accounts_event(jwt)

    # assert balance and last updated timestamp prior to api invocation
    account = walter_db.get_account("user-003", "acct-004")
    assert account.balance == 0.0
    assert "2025-06-01" in account.balance_last_updated_at.isoformat()

    # invoke api
    actual_response = get_accounts_api.invoke(event)

    # assert that balance and balance last update timestamp were updated
    assert actual_response.data["accounts"][0]["balance"] == 50.00
    assert (
        "2025-07-01" in actual_response.data["accounts"][0]["balance_last_updated_at"]
    )
