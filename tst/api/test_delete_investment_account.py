import pytest

from src.api.common.models import HTTPStatus, Status
from src.api.accounts.investments.delete_investment_account import (
    DeleteInvestmentAccount,
)
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from tst.api.utils import get_delete_investment_account_event


@pytest.fixture
def delete_investment_account_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
) -> DeleteInvestmentAccount:
    return DeleteInvestmentAccount(walter_authenticator, walter_cw, walter_db)


def test_delete_investment_account_success(
    delete_investment_account_api: DeleteInvestmentAccount, jwt_walter: str
) -> None:
    """Test successful deletion of an investment account."""
    # Investment account ID to delete from the test data
    account_id = "94b1ddd5-a35d-438a-86c7-6c419d653a6a"

    delete_investment_account_event = get_delete_investment_account_event(
        token=jwt_walter, account_id=account_id
    )

    delete_investment_account_response = delete_investment_account_api.invoke(
        delete_investment_account_event
    )

    assert delete_investment_account_response.api_name == "DeleteInvestmentAccount"
    assert delete_investment_account_response.http_status == HTTPStatus.OK
    assert delete_investment_account_response.status == Status.SUCCESS
    assert (
        delete_investment_account_response.message
        == "Successfully deleted investment account!"
    )


def test_delete_investment_account_failure_not_authenticated(
    delete_investment_account_api: DeleteInvestmentAccount,
) -> None:
    """Test failure when authentication token is invalid."""
    account_id = "94b1ddd5-a35d-438a-86c7-6c419d653a6a"

    delete_investment_account_event = get_delete_investment_account_event(
        token="INVALID_TOKEN", account_id=account_id
    )

    delete_investment_account_response = delete_investment_account_api.invoke(
        delete_investment_account_event
    )

    assert delete_investment_account_response.api_name == "DeleteInvestmentAccount"
    assert delete_investment_account_response.http_status == HTTPStatus.OK
    assert delete_investment_account_response.status == Status.FAILURE
    assert (
        delete_investment_account_response.message
        == "Not authenticated! Token is invalid."
    )


def test_delete_investment_account_failure_user_does_not_exist(
    delete_investment_account_api: DeleteInvestmentAccount,
    walter_authenticator: WalterAuthenticator,
) -> None:
    """Test failure when user does not exist."""
    account_id = "94b1ddd5-a35d-438a-86c7-6c419d653a6a"

    # Generate a token for a non-existent user
    nonexistent_token = walter_authenticator.generate_user_token(
        "nonexistent@gmail.com"
    )

    delete_investment_account_event = get_delete_investment_account_event(
        token=nonexistent_token, account_id=account_id
    )

    delete_investment_account_response = delete_investment_account_api.invoke(
        delete_investment_account_event
    )

    assert delete_investment_account_response.api_name == "DeleteInvestmentAccount"
    assert delete_investment_account_response.http_status == HTTPStatus.OK
    assert delete_investment_account_response.status == Status.FAILURE
    assert "does not exist" in delete_investment_account_response.message


def test_delete_investment_account_failure_account_does_not_exist(
    delete_investment_account_api: DeleteInvestmentAccount, jwt_walter: str
) -> None:
    """Test failure when investment account does not exist."""
    delete_investment_account_event = get_delete_investment_account_event(
        token=jwt_walter, account_id="INVALID_INVESTMENT_ACCOUNT_ID"
    )

    delete_investment_account_response = delete_investment_account_api.invoke(
        delete_investment_account_event
    )

    assert delete_investment_account_response.api_name == "DeleteInvestmentAccount"
    assert delete_investment_account_response.http_status == HTTPStatus.OK
    assert delete_investment_account_response.status == Status.FAILURE
    assert (
        delete_investment_account_response.message
        == "Investment account does not exist!"
    )
