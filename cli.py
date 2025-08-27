import json
from typing import Optional

import typer

from src.api.routing.router import APIRouter
from src.canaries.routing.router import CanaryRouter, CanaryType
from src.clients import (
    add_transaction_api,
    create_account_api,
    create_link_token_api,
    create_user_api,
    delete_account_api,
    delete_transaction_api,
    get_accounts_api,
    get_transactions_api,
    get_user_api,
    login_api,
    logout_api,
    refresh_api,
    update_account_api,
)
from src.database.transactions.models import TransactionType
from src.utils.log import Logger
from src.workflows.common.router import WorkflowRouter

log = Logger(__name__).get_logger()


def create_api_event(
    token: Optional[str] = None, query_params: Optional[dict] = None, **kwargs
) -> dict:
    """
    Create an API event with the provided token and kwargs.

    This method is used to create API events for testing with the CLI. This method
    ensures the event is formatted correctly for the API. However, the created
    event includes no information about path or method as the CLI does not use
    the API router. The APIs are called directly with their respective methods.

    Args:
        token: The authentication token to include in the event for authenticated APIs.
        query_params: The query parameters to include in the event.
        **kwargs: The additional kwargs to include in the event as body.

    Returns:
        Properly formatted event for testing with the CLI.
    """
    event = {}

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
    event = create_api_event(email=email, password=password)
    response = login_api.invoke(event, emit_metrics=False).to_json()
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
    event = create_api_event(token=refresh_token)
    response = refresh_api.invoke(event, emit_metrics=False).to_json()
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
    event = create_api_event(token=access_token)
    response = logout_api.invoke(event, emit_metrics=False).to_json()
    log.info(f"WalterCLI: Response:\n{parse_response(response)}")


# USERS


@app.command()
def get_user(token: str = None) -> None:
    log.info("WalterCLI: Getting user...")
    event = create_api_event(token)
    response = get_user_api.invoke(event, emit_metrics=False).to_json()
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
    event = create_api_event(
        email=email, first_name=first_name, last_name=last_name, password=password
    )
    response = create_user_api.invoke(event, emit_metrics=False).to_json()
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
    event = create_api_event(token)
    response = get_accounts_api.invoke(event, emit_metrics=False).to_json()
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
    event = create_api_event(
        token,
        account_type=account_type,
        account_subtype=account_subtype,
        institution_name=institution_name,
        account_name=account_name,
        account_mask=account_mask,
        balance=balance,
    )
    response = create_account_api.invoke(event, emit_metrics=False).to_json()
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
    event = create_api_event(
        token,
        account_id=account_id,
        account_type=account_type,
        account_subtype=account_subtype,
        institution_name=institution_name,
        account_name=account_name,
        account_mask=account_mask,
        balance=balance,
        logo_url=logo_url,
    )
    response = update_account_api.invoke(event, emit_metrics=False).to_json()
    log.info(f"WalterCLI: UpdateAccount Response:\n{parse_response(response)}")


@app.command()
def delete_account(
    token: str = typer.Option(None, help="JWT token for the authenticated user"),
    account_id: str = typer.Option(None, help="The account ID to delete"),
) -> None:
    """Delete an account (and its transactions) for the authenticated user."""
    log.info("WalterCLI: DeleteAccount")
    event = create_api_event(token, account_id=account_id)
    response = delete_account_api.invoke(event, emit_metrics=False).to_json()
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
    event = create_api_event(
        token,
        query_params={"start_date": start_date, "end_date": end_date},
    )
    if account_id:
        event["queryStringParameters"]["account_id"] = account_id
    response = get_transactions_api.invoke(event, emit_metrics=False).to_json()
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

    event = create_api_event(
        token=token,
        query_params={},
        **kwargs,
    )
    response = add_transaction_api.invoke(event, emit_metrics=False).to_json()
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
    event = create_api_event(
        token,
        query_params={},
        transaction_date=transaction_date,
        transaction_id=transaction_id,
        updated_date=date,
        updated_vendor=vendor,
        updated_amount=amount,
        updated_category=category,
    )
    response = APIRouter.get_method(event, emit_metrics=False).invoke(event).to_json()
    log.info(f"WalterCLI: EditTransaction Response:\n{parse_response(response)}")


@app.command()
def delete_transaction(
    token: str = None, date: str = None, transaction_id: str = None
) -> None:
    log.info("WalterCLI: DeleteTransaction")
    event = create_api_event(token, date=date, transaction_id=transaction_id)
    response = delete_transaction_api.invoke(event, emit_metrics=False).to_json()
    log.info(f"WalterCLI: DeleteTransaction Response:\n{parse_response(response)}")


# PLAID


@app.command()
def create_link_token(token: str = None) -> None:
    log.info("WalterCLI: CreateLinkToken")
    event = create_api_event(token)
    response = create_link_token_api.invoke(event, emit_metrics=False).to_json()
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
        response = CanaryRouter.get_canary(canary_type).invoke(emit_metrics=False)
        log.info(f"WalterCLI: Canary Response:\n{parse_response(response)}")
    else:
        log.info("Invoking all canaries")
        for canary_type in CanaryType:
            response = CanaryRouter.get_canary(canary_type).invoke(emit_metrics=False)
            log.info(f"WalterCLI: {canary_type} Response:\n{parse_response(response)}")


#############
# WORKFLOWS #
#############


def get_workflow_event(workflow_name: str) -> dict:
    return {
        "workflow_name": workflow_name,
    }


@app.command()
def update_security_prices() -> None:
    workflow_name = "UpdateSecurityPrices"
    log.info(f"WalterCLI: {workflow_name}")
    event = get_workflow_event(workflow_name)
    response = WorkflowRouter.get_workflow(event).invoke(event).to_json()
    log.info(f"WalterCLI: {workflow_name}:\n{json.dumps(response, indent=4)}")


if __name__ == "__main__":
    app()
