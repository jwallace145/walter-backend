import pytest

from src.api.common.models import HTTPStatus, Status
from src.api.accounts.investments.get_investment_accounts import GetInvestmentAccounts
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from tst.api.utils import get_get_investment_accounts_event


@pytest.fixture
def get_investment_accounts_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
) -> GetInvestmentAccounts:
    return GetInvestmentAccounts(walter_authenticator, walter_cw, walter_db)


def test_get_investment_accounts_success(
    get_investment_accounts_api: GetInvestmentAccounts, jwt_walter: str
) -> None:
    """Test successful retrieval of investment accounts."""
    get_investment_accounts_event = get_get_investment_accounts_event(token=jwt_walter)
    get_investment_accounts_response = get_investment_accounts_api.invoke(
        get_investment_accounts_event
    )

    assert get_investment_accounts_response.api_name == "GetInvestmentAccounts"
    assert get_investment_accounts_response.http_status == HTTPStatus.OK
    assert get_investment_accounts_response.status == Status.SUCCESS
    assert (
        get_investment_accounts_response.message
        == "Successfully retrieved investment accounts!"
    )

    # Verify response data structure
    assert "total_num_investment_accounts" in get_investment_accounts_response.data
    assert "total_investment_balance" in get_investment_accounts_response.data
    assert "investment_accounts" in get_investment_accounts_response.data

    # Verify we have at least one investment account in the test data
    assert get_investment_accounts_response.data["total_num_investment_accounts"] > 0
    assert isinstance(
        get_investment_accounts_response.data["investment_accounts"], list
    )


def test_get_investment_accounts_failure_not_authenticated(
    get_investment_accounts_api: GetInvestmentAccounts,
) -> None:
    """Test failure when authentication token is invalid."""
    get_investment_accounts_event = get_get_investment_accounts_event(
        token="INVALID_TOKEN"
    )
    get_investment_accounts_response = get_investment_accounts_api.invoke(
        get_investment_accounts_event
    )

    assert get_investment_accounts_response.api_name == "GetInvestmentAccounts"
    assert get_investment_accounts_response.http_status == HTTPStatus.OK
    assert get_investment_accounts_response.status == Status.FAILURE
    assert (
        get_investment_accounts_response.message
        == "Not authenticated! Token is invalid."
    )


def test_get_investment_accounts_failure_user_does_not_exist(
    get_investment_accounts_api: GetInvestmentAccounts,
    walter_authenticator: WalterAuthenticator,
) -> None:
    """Test failure when user does not exist."""
    # Generate a token for a non-existent user
    nonexistent_token = walter_authenticator.generate_user_token(
        "nonexistent@gmail.com"
    )
    get_investment_accounts_event = get_get_investment_accounts_event(
        token=nonexistent_token
    )
    get_investment_accounts_response = get_investment_accounts_api.invoke(
        get_investment_accounts_event
    )

    assert get_investment_accounts_response.api_name == "GetInvestmentAccounts"
    assert get_investment_accounts_response.http_status == HTTPStatus.OK
    assert get_investment_accounts_response.status == Status.FAILURE
    assert "does not exist" in get_investment_accounts_response.message
