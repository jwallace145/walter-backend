import pytest

from src.api.accounts.get_accounts import GetAccounts
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


def _event_with_auth(token: str) -> dict:
    return {
        "headers": {"Authorization": f"Bearer {token}"},
        "queryStringParameters": None,
        "body": None,
    }


def test_get_accounts_success(
    get_accounts_api: GetAccounts, walter_db: WalterDB, jwt_walter: str
) -> None:
    # prepare event
    event = _event_with_auth(jwt_walter)

    # expected data from DB
    user = walter_db.get_user_by_email("walter@gmail.com")
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


def test_get_accounts_failure_not_authenticated(
    get_accounts_api: GetAccounts,
) -> None:
    event = _event_with_auth("invalid-token")
    expected_response = get_expected_response(
        api_name=get_accounts_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Not authenticated! Token is invalid.",
    )
    assert expected_response == get_accounts_api.invoke(event)


def test_get_accounts_failure_user_does_not_exist(
    get_accounts_api: GetAccounts, walter_authenticator: WalterAuthenticator
) -> None:
    # create a valid JWT for a non-existent user
    ghost_token = walter_authenticator.generate_user_token("ghost@ghost.com")
    event = _event_with_auth(ghost_token)
    expected_response = get_expected_response(
        api_name=get_accounts_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="User with email 'ghost@ghost.com' does not exist!",
    )
    assert expected_response == get_accounts_api.invoke(event)
