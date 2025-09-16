import json
from typing import Optional

import typer

from src.api.routing.router import APIRouter
from src.canaries.routing.router import CanaryRouter, CanaryType
from src.database.transactions.models import TransactionType
from src.utils.log import Logger
from src.workflows.common.router import WorkflowRouter

log = Logger(__name__).get_logger()


def create_api_event(
    http_path: str = None,
    http_method: str = None,
    token: Optional[str] = None,
    query_params: Optional[dict] = None,
    **kwargs,
) -> dict:
    """
    Create an API event with the provided token and kwargs.

    This method is used to create API events for testing with the CLI. This method
    ensures the event is formatted correctly for the API. However, the created
    event includes no information about path or method as the CLI does not use
    the API router. The APIs are called directly with their respective methods.

    Args:
        http_path: The HTTP path to include in the event.
        http_method: The HTTP method to include in the event.
        token: The authentication token to include in the event for authenticated APIs.
        query_params: The query parameters to include in the event.
        **kwargs: The additional kwargs to include in the event as body.

    Returns:
        Properly formatted event for testing with the CLI.
    """
    event = {}

    event["path"] = http_path
    event["httpMethod"] = http_method

    # set request ID for CLI invocations
    event["requestContext"] = {}
    event["requestContext"]["requestId"] = "WALTER_BACKEND_CLI_REQUEST"

    # if api token is provided, add it to the event
    if token:
        event["headers"] = {"Authorization": f"Bearer {token}"}

    if query_params and len(query_params) > 0:
        event["queryStringParameters"] = query_params

    # if additional kwargs are provided, add them to the event as body
    if kwargs:
        headers = event.get("headers", {})
        headers["content-type"] = "application/json"
        event["headers"] = headers
        event.get("headers", {})["content-type"] = "application/json"
        event["body"] = json.dumps(kwargs)

    return event


def parse_response(response: dict) -> str:
    response["body"] = json.loads(response["body"])
    return json.dumps(response, indent=4)


##############
# WALTER CLI #
##############

app = typer.Typer()

# AUTHENTICATION


@app.command()
def login(
    email: str = typer.Option(None, help="Email address for authentication"),
    password: str = typer.Option(None, help="Account password"),
) -> None:
    """Login to generate authentication tokens.

    Generates a valid long-lived refresh token and short-lived access token on successful
    authentication. Starts a new user session which is persisted to the database.

    Parameters:
    - email: Valid email address associated with account (required)
    - password: Account password (required)
    """
    log.info("WalterCLI: Login")
    event: dict = create_api_event(
        http_path="/auth/login", http_method="POST", email=email, password=password
    )
    response: dict = (
        APIRouter().get_method(event).invoke(event, emit_metrics=False).to_json()
    )
    log.info(f"WalterCLI: Response:\n{parse_response(response)}")


@app.command()
def refresh(
    refresh_token: str = typer.Option(
        None, help="Valid refresh token to get new access token"
    )
) -> None:
    """Get new access token using refresh token.

    Returns a new short-lived access token when provided with a valid refresh token.
    This allows getting new access tokens without re-authenticating with credentials.

    Parameters:
    - refresh_token: Valid refresh token obtained from login (required)
    """
    log.info("WalterCLI: Refresh")
    event: dict = create_api_event(
        http_path="/auth/refresh", http_method="POST", token=refresh_token
    )
    response: dict = (
        APIRouter().get_method(event).invoke(event, emit_metrics=False).to_json()
    )
    log.info(f"WalterCLI: Response:\n{parse_response(response)}")


@app.command()
def logout(
    access_token: str = typer.Option(None, help="Access token to invalidate session")
) -> None:
    """Logout and revoke authentication tokens.

    Logs out user by revoking both refresh and access tokens for the current session.
    Any devices still using these tokens will be forced to reauthenticate.

    Parameters:
    - access_token: Valid access token for the session to end (required)
    """
    log.info("WalterCLI: Logout")
    event: dict = create_api_event(
        http_path="/auth/logout", http_method="POST", token=access_token
    )
    response: dict = (
        APIRouter().get_method(event).invoke(event, emit_metrics=False).to_json()
    )
    log.info(f"WalterCLI: Response:\n{parse_response(response)}")


# USERS


@app.command()
def get_user(token: str = None) -> None:
    log.info("WalterCLI: Getting user...")
    event: dict = create_api_event(http_path="/users", http_method="GET", token=token)
    response: dict = (
        APIRouter().get_method(event).invoke(event, emit_metrics=False).to_json()
    )
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def create_user(
    email: str = typer.Option(None, help="Email address for the new user"),
    first_name: str = typer.Option(None, help="User's first name"),
    last_name: str = typer.Option(None, help="User's last name"),
    password: str = typer.Option(None, help="Password for the account"),
) -> None:
    """Create a new user account.

    Creates a new user with the provided details. The email must be valid and unique.
    The password must meet the minimum security requirements.

    Parameters:
    - email: Valid email address for the new user (required)
    - first_name: User's first name (required)
    - last_name: User's last name (required)
    - password: Password that meets security requirements (required)
    """
    log.info("Walter CLI: Creating user...")
    event: dict = create_api_event(
        http_path="/users",
        http_method="POST",
        email=email,
        first_name=first_name,
        last_name=last_name,
        password=password,
    )
    response: dict = (
        APIRouter().get_method(event).invoke(event, emit_metrics=False).to_json()
    )
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


# ACCOUNTS


@app.command()
def get_accounts(
    token: str = typer.Option(None, help="JWT token for the authenticated user")
) -> None:
    """Get all accounts for the authenticated user.

    Parameters:
    - token: Bearer JWT for the user (required)
    """
    log.info("WalterCLI: GetAccounts")
    event: dict = create_api_event(
        http_path="/accounts",
        http_method="GET",
        token=token,
    )
    response: dict = (
        APIRouter().get_method(event).invoke(event, emit_metrics=False).to_json()
    )
    log.info(f"WalterCLI: GetAccounts Response:\n{parse_response(response)}")


@app.command()
def create_account(
    token: str = typer.Option(None, help="JWT token for the authenticated user"),
    account_type: str = typer.Option(
        None, help="Account type (e.g., credit, depository, investment)"
    ),
    account_subtype: str = typer.Option(
        None, help="Account subtype (e.g., credit card, checking, brokerage)"
    ),
    institution_name: str = typer.Option(
        None, help="Name of the financial institution"
    ),
    account_name: str = typer.Option(None, help="Account display name"),
    account_mask: str = typer.Option(
        None, help="Last 2-4 digits used to identify the account"
    ),
    balance: float = typer.Option(None, help="Current account balance"),
) -> None:
    """Create a new account for the authenticated user."""
    log.info("WalterCLI: CreateAccount")
    event: dict = create_api_event(
        http_path="/accounts",
        http_method="POST",
        token=token,
        account_type=account_type,
        account_subtype=account_subtype,
        institution_name=institution_name,
        account_name=account_name,
        account_mask=account_mask,
        balance=balance,
    )
    response: dict = (
        APIRouter().get_method(event).invoke(event, emit_metrics=False).to_json()
    )
    log.info(f"WalterCLI: CreateAccount Response:\n{parse_response(response)}")


@app.command()
def update_account(
    token: str = typer.Option(None, help="JWT token for the authenticated user"),
    account_id: str = typer.Option(None, help="The account ID to update"),
    account_type: str = typer.Option(
        None, help="Updated account type (credit, depository, investment)"
    ),
    account_subtype: str = typer.Option(
        None, help="Updated account subtype (e.g., credit card, checking, brokerage)"
    ),
    institution_name: str = typer.Option(None, help="Updated institution name"),
    account_name: str = typer.Option(None, help="Updated account name"),
    account_mask: str = typer.Option(None, help="Updated account mask (last digits)"),
    balance: float = typer.Option(None, help="Updated account balance"),
    logo_url: str = typer.Option(None, help="Institution/account logo URL"),
) -> None:
    """Update an existing account for the authenticated user."""
    log.info("WalterCLI: UpdateAccount")
    event: dict = create_api_event(
        http_path="/accounts",
        http_method="PUT",
        token=token,
        account_id=account_id,
        account_type=account_type,
        account_subtype=account_subtype,
        institution_name=institution_name,
        account_name=account_name,
        account_mask=account_mask,
        balance=balance,
        logo_url=logo_url,
    )
    response: dict = (
        APIRouter().get_method(event).invoke(event, emit_metrics=False).to_json()
    )
    log.info(f"WalterCLI: UpdateAccount Response:\n{parse_response(response)}")


@app.command()
def delete_account(
    token: str = typer.Option(None, help="JWT token for the authenticated user"),
    account_id: str = typer.Option(None, help="The account ID to delete"),
) -> None:
    """Delete an account (and its transactions) for the authenticated user."""
    log.info("WalterCLI: DeleteAccount")
    event: dict = create_api_event(
        http_path="/accounts", http_method="DELETE", token=token, account_id=account_id
    )
    response: dict = (
        APIRouter().get_method(event).invoke(event, emit_metrics=False).to_json()
    )
    log.info(f"WalterCLI: DeleteAccount Response:\n{parse_response(response)}")


# TRANSACTIONS


@app.command()
def get_transactions(
    token: str = None,
    account_id: str = None,
    start_date: str = None,
    end_date: str = None,
) -> None:
    log.info("WalterCLI: GetTransactions")
    event: dict = create_api_event(
        http_path="/transactions",
        http_method="GET",
        token=token,
        query_params={"start_date": start_date, "end_date": end_date},
    )
    if account_id:
        event["queryStringParameters"]["account_id"] = account_id
    response: dict = (
        APIRouter().get_method(event).invoke(event, emit_metrics=False).to_json()
    )
    log.info(f"WalterCLI: GetTransactions Response:\n{parse_response(response)}")


@app.command()
def add_transaction(
    token: str = None,
    account_id: str = None,
    date: str = None,
    amount: float = None,
    transaction_type: str = None,
    transaction_subtype: str = None,
    transaction_category: str = None,
    security_id: str = None,
    security_type: str = None,
    quantity: float = None,
    price_per_share: float = None,
    merchant_name: str = None,
) -> None:
    log.info("WalterCLI: AddTransaction")

    kwargs = {
        "account_id": account_id,
        "transaction_type": transaction_type,
        "transaction_subtype": transaction_subtype,
        "transaction_category": transaction_category,
        "date": date,
        "amount": amount,
    }

    match TransactionType.from_string(transaction_type):
        case TransactionType.BANKING:
            kwargs["merchant_name"] = merchant_name
        case TransactionType.INVESTMENT:
            kwargs["security_id"] = security_id
            kwargs["security_type"] = security_type
            kwargs["quantity"] = quantity
            kwargs["price_per_share"] = price_per_share

    event: dict = create_api_event(
        http_path="/transactions",
        http_method="POST",
        token=token,
        query_params={},
        **kwargs,
    )
    response: dict = (
        APIRouter().get_method(event).invoke(event, emit_metrics=False).to_json()
    )
    log.info(f"WalterCLI: AddTransaction Response:\n{parse_response(response)}")


@app.command()
def edit_transaction(
    token: str = None,
    transaction_date: str = None,
    transaction_id: str = None,
    date: str = None,
    vendor: str = None,
    amount: float = None,
    category: str = None,
) -> None:
    log.info("WalterCLI: EditTransaction")
    event: dict = create_api_event(
        http_path="/transactions",
        http_method="PUT",
        token=token,
        query_params={},
        transaction_date=transaction_date,
        transaction_id=transaction_id,
        updated_date=date,
        updated_vendor=vendor,
        updated_amount=amount,
        updated_category=category,
    )
    response: dict = (
        APIRouter().get_method(event).invoke(event, emit_metrics=False).to_json()
    )
    log.info(f"WalterCLI: EditTransaction Response:\n{parse_response(response)}")


@app.command()
def delete_transaction(
    token: str = None, date: str = None, transaction_id: str = None
) -> None:
    log.info("WalterCLI: DeleteTransaction")
    event: dict = create_api_event(
        http_path="/transactions",
        http_method="DELETE",
        token=token,
        date=date,
        transaction_id=transaction_id,
    )
    response: dict = (
        APIRouter().get_method(event).invoke(event, emit_metrics=False).to_json()
    )
    log.info(f"WalterCLI: DeleteTransaction Response:\n{parse_response(response)}")


# PLAID


@app.command()
def create_link_token(token: str = None) -> None:
    log.info("WalterCLI: CreateLinkToken")
    event: dict = create_api_event(
        http_path="/plaid/create-link-token", http_method="POST", token=token
    )
    response: dict = (
        APIRouter().get_method(event).invoke(event, emit_metrics=False).to_json()
    )
    log.info(f"WalterCLI: CreateLinkToken Response:\n{parse_response(response)}")


############
# CANARIES #
############


@app.command()
def canary(
    api: str = typer.Option(
        None,
        help=f"The name of the API the canary invokes. Defaults to None which invokes all canaries. Valid canary options: {[canary.value for canary in CanaryType]})",
    )
) -> None:
    """
    This CLI command invokes a canary to test API endpoints.

    The canary is invoked using the specified API. If no API is specified, all canaries are invoked.
    """
    log.info("WalterCLI: Canary")
    if api:
        log.info(f"Invoking canary for '{api}'")
        canary_type = CanaryType.from_string(api)
        response = CanaryRouter().get_canary(canary_type).invoke(emit_metrics=False)
        log.info(f"WalterCLI: Canary Response:\n{parse_response(response)}")
    else:
        log.info("Invoking all canaries")
        for canary_type in CanaryType:
            response = CanaryRouter().get_canary(canary_type).invoke(emit_metrics=False)
            log.info(f"WalterCLI: {canary_type} Response:\n{parse_response(response)}")


#############
# WORKFLOWS #
#############


def get_workflow_event(workflow_name: str) -> dict:
    return {
        "workflow_name": workflow_name,
    }


@app.command()
def update_prices() -> None:
    workflow_name = "UpdateSecurityPrices"
    log.info(f"WalterCLI: {workflow_name}")
    event: dict = get_workflow_event(workflow_name)
    response: dict = (
        WorkflowRouter().get_workflow(event).invoke(event, emit_metrics=False).to_json()
    )
    log.info(f"WalterCLI: {workflow_name}:\n{json.dumps(response, indent=4)}")


if __name__ == "__main__":
    app()
