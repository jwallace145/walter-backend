import pytest
from freezegun import freeze_time

from src.api.accounts.get_accounts.method import GetAccounts
from src.api.common.models import HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from tst.api.utils import get_expected_response


@pytest.fixture
def get_accounts_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
) -> GetAccounts:
    return GetAccounts(walter_authenticator, walter_cw, walter_db)


def create_get_accounts_event(token: str) -> dict:
    return {
        "path": "/accounts",
        "httpMethod": "GET",
        "headers": {"Authorization": f"Bearer {token}"},
        "queryStringParameters": None,
        "body": None,
    }


@freeze_time("2025-07-01")
def test_get_accounts_success(
    get_accounts_api: GetAccounts,
    walter_db: WalterDB,
    walter_authenticator: WalterAuthenticator,
) -> None:
    # prepare event
    user_id = "user-001"
    session_id = "session-001"
    account_ids = {"acct-001", "acct-008"}
    access_token, access_token_expiry = walter_authenticator.generate_access_token(
        user_id, session_id
    )
    event = create_get_accounts_event(access_token)

    # invoke api
    response = get_accounts_api.invoke(event)

    # assert response
    assert response.data["user_id"] == user_id
    assert response.data["total_num_accounts"] == 2
    assert response.data["total_balance"] == 25000.00

    actual_account_ids = {data["account_id"] for data in response.data["accounts"]}
    assert actual_account_ids == account_ids

    # create account ids to accounts map for fast lookup by account id
    account_ids_to_account = {}
    for account in response.data["accounts"]:
        account_ids_to_account[account["account_id"]] = account

    # assert credit card account
    assert account_ids_to_account["acct-001"]["account_id"] == "acct-001"
    assert account_ids_to_account["acct-001"]["institution_name"] == "Test Credit Bank"
    assert account_ids_to_account["acct-001"]["account_name"] == "Walter Credit Account"
    assert account_ids_to_account["acct-001"]["account_type"] == "credit"
    assert account_ids_to_account["acct-001"]["account_subtype"] == "credit card"
    assert account_ids_to_account["acct-001"]["balance"] == 0.0

    # assert investment account
    assert account_ids_to_account["acct-008"]["account_id"] == "acct-008"
    assert (
        account_ids_to_account["acct-008"]["institution_name"] == "Test Investment Bank"
    )
    assert (
        account_ids_to_account["acct-008"]["account_name"]
        == "Walter Investment Account"
    )
    assert account_ids_to_account["acct-008"]["account_type"] == "investment"
    assert account_ids_to_account["acct-008"]["account_subtype"] == "retirement"
    assert account_ids_to_account["acct-008"]["balance"] == 25000.00
    assert len(account_ids_to_account["acct-008"]["holdings"]) == 1
    assert (
        account_ids_to_account["acct-008"]["holdings"][0]["security_id"]
        == "sec-nyse-coke"
    )
    assert (
        account_ids_to_account["acct-008"]["holdings"][0]["security_ticker"] == "COKE"
    )
    assert (
        account_ids_to_account["acct-008"]["holdings"][0]["security_name"]
        == "Coca-Cola Consolidated Inc."
    )
    assert account_ids_to_account["acct-008"]["holdings"][0]["quantity"] == 100.00
    assert account_ids_to_account["acct-008"]["holdings"][0]["current_price"] == 250.00
    assert account_ids_to_account["acct-008"]["holdings"][0]["total_value"] == 25000.00
    assert (
        account_ids_to_account["acct-008"]["holdings"][0]["total_cost_basis"] == 1000.00
    )
    assert (
        account_ids_to_account["acct-008"]["holdings"][0]["average_cost_basis"] == 10.00
    )
    assert account_ids_to_account["acct-008"]["holdings"][0]["gain_loss"] == 24000.00


@freeze_time("2025-07-01")
def test_get_accounts_failure_not_authenticated(
    get_accounts_api: GetAccounts,
) -> None:
    event = create_get_accounts_event("invalid-token")
    expected_response = get_expected_response(
        api_name=get_accounts_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Not authenticated! Token is expired or invalid.",
    )
    assert expected_response == get_accounts_api.invoke(event)


@freeze_time("2025-07-01")
def test_get_accounts_failure_session_does_not_exist(
    get_accounts_api: GetAccounts, walter_authenticator: WalterAuthenticator
) -> None:
    # create a valid JWT for a non-existent user
    token, token_expiry = walter_authenticator.generate_access_token(
        "user-ghost", "jti-ghost"
    )
    event = create_get_accounts_event(token)
    expected_response = get_expected_response(
        api_name=get_accounts_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Not authenticated! Session does not exist.",
    )
    assert expected_response == get_accounts_api.invoke(event)


@freeze_time("2025-07-01")
def test_get_accounts_success_update_balances(
    get_accounts_api: GetAccounts,
    walter_db: WalterDB,
    walter_authenticator: WalterAuthenticator,
) -> None:
    user_id = "user-003"
    session_id = "session-002"
    account_id = "acct-004"
    token, token_expiry = walter_authenticator.generate_access_token(
        user_id, session_id
    )
    event = create_get_accounts_event(token)

    # assert balance and last updated timestamp prior to api invocation
    account = walter_db.get_account(user_id, account_id)
    assert account.balance == 0.0
    assert "2025-06-01" in account.balance_last_updated_at.isoformat()

    # invoke api
    actual_response = get_accounts_api.invoke(event)

    # assert that balance and balance last update timestamp were updated
    assert actual_response.data["accounts"][0]["balance"] == 50.00
