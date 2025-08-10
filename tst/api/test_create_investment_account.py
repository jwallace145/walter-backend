import pytest

from src.api.common.models import HTTPStatus, Status
from src.api.accounts.investments.create_investment_account import (
    CreateInvestmentAccount,
)
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from tst.api.utils import get_create_investment_account_event


@pytest.fixture
def create_investment_account_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
) -> CreateInvestmentAccount:
    return CreateInvestmentAccount(walter_authenticator, walter_cw, walter_db)


def test_create_investment_account_success(
    create_investment_account_api: CreateInvestmentAccount, jwt_walter: str
) -> None:
    """Test successful creation of an investment account."""
    bank_name = "Vanguard"
    account_name = "Test Investment Account"
    account_last_four_numbers = "1234"

    create_investment_account_event = get_create_investment_account_event(
        token=jwt_walter,
        bank_name=bank_name,
        account_name=account_name,
        account_last_four_numbers=account_last_four_numbers,
    )

    create_investment_account_response = create_investment_account_api.invoke(
        create_investment_account_event
    )

    assert create_investment_account_response.api_name == "CreateInvestmentAccount"
    assert create_investment_account_response.http_status == HTTPStatus.CREATED
    assert create_investment_account_response.status == Status.SUCCESS
    assert (
        create_investment_account_response.message
        == "Investment account created successfully!"
    )

    # Verify response data structure
    assert "investment_account" in create_investment_account_response.data

    # Verify the created account details
    created_account = create_investment_account_response.data["investment_account"]
    assert created_account["bank_name"] == bank_name
    assert created_account["account_name"] == account_name
    assert created_account["account_last_four_numbers"] == account_last_four_numbers
    assert created_account["balance"] == 0.0  # Default balance


def test_create_investment_account_failure_not_authenticated(
    create_investment_account_api: CreateInvestmentAccount,
) -> None:
    """Test failure when authentication token is invalid."""
    bank_name = "Vanguard"
    account_name = "Test Investment Account"
    account_last_four_numbers = "1234"

    create_investment_account_event = get_create_investment_account_event(
        token="INVALID_TOKEN",
        bank_name=bank_name,
        account_name=account_name,
        account_last_four_numbers=account_last_four_numbers,
    )

    create_investment_account_response = create_investment_account_api.invoke(
        create_investment_account_event
    )

    assert create_investment_account_response.api_name == "CreateInvestmentAccount"
    assert create_investment_account_response.http_status == HTTPStatus.OK
    assert create_investment_account_response.status == Status.FAILURE
    assert (
        create_investment_account_response.message
        == "Not authenticated! Token is invalid."
    )


def test_create_investment_account_failure_user_does_not_exist(
    create_investment_account_api: CreateInvestmentAccount,
    walter_authenticator: WalterAuthenticator,
) -> None:
    """Test failure when user does not exist."""
    bank_name = "Vanguard"
    account_name = "Test Investment Account"
    account_last_four_numbers = "1234"

    # Generate a token for a non-existent user
    nonexistent_token = walter_authenticator.generate_user_token(
        "nonexistent@gmail.com"
    )

    create_investment_account_event = get_create_investment_account_event(
        token=nonexistent_token,
        bank_name=bank_name,
        account_name=account_name,
        account_last_four_numbers=account_last_four_numbers,
    )

    create_investment_account_response = create_investment_account_api.invoke(
        create_investment_account_event
    )

    assert create_investment_account_response.api_name == "CreateInvestmentAccount"
    assert create_investment_account_response.http_status == HTTPStatus.OK
    assert create_investment_account_response.status == Status.FAILURE
    assert "does not exist" in create_investment_account_response.message


def test_create_investment_account_success_with_empty_fields(
    create_investment_account_api: CreateInvestmentAccount,
    jwt_walter: str,
) -> None:
    """Test successful creation even with empty fields (API doesn't validate empty strings)."""
    # Create an event with empty bank_name
    create_investment_account_event = get_create_investment_account_event(
        token=jwt_walter,
        bank_name="",  # Empty bank_name is still accepted
        account_name="Test Investment Account",
        account_last_four_numbers="1234",
    )

    create_investment_account_response = create_investment_account_api.invoke(
        create_investment_account_event
    )

    assert create_investment_account_response.api_name == "CreateInvestmentAccount"
    assert create_investment_account_response.http_status == HTTPStatus.CREATED
    assert create_investment_account_response.status == Status.SUCCESS
    assert (
        create_investment_account_response.message
        == "Investment account created successfully!"
    )

    # Verify the created account has the empty bank_name
    created_account = create_investment_account_response.data["investment_account"]
    assert created_account["bank_name"] == ""
