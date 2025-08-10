import json

import typer

from src.api.routing.router import APIRouter
from src.canaries.routing.router import CanaryRouter
from src.utils.log import Logger
from tst.api.utils import (
    get_auth_user_event,
    get_create_user_event,
    get_get_user_event,
    get_add_stock_event,
    get_portfolio_event,
    get_get_stock_event,
    get_get_prices_event,
    get_get_transactions_event,
    get_add_transaction_event,
    get_edit_transaction_event,
    get_delete_transaction_event,
    get_get_cash_accounts_event,
    get_update_cash_account_event,
    get_create_cash_account_event,
    get_delete_cash_account_event,
    get_create_link_token_event,
    get_exchange_public_token_event,
    get_sync_transactions_event,
    get_delete_stock_event,
    get_create_credit_account_event,
    get_get_credit_accounts_event,
    get_delete_credit_account_event,
    get_create_investment_account_event,
    get_get_investment_accounts_event,
    get_delete_investment_account_event,
)

log = Logger(__name__).get_logger()

CONTEXT = {}


def parse_response(response: dict) -> str:
    response["body"] = json.loads(response["body"])
    return json.dumps(response, indent=4)


##############
# WALTER CLI #
##############

app = typer.Typer()

# AUTHENTICATION


@app.command()
def auth_user(email: str = None, password: str = None) -> None:
    log.info("Walter CLI: Authenticating user...")
    event = get_auth_user_event(email, password)
    response = APIRouter.get_method(event).invoke(event).to_json()
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


# USERS


@app.command()
def get_user(token: str = None) -> None:
    log.info("Walter CLI: Getting user...")
    event = get_get_user_event(token)
    response = APIRouter.get_method(event).invoke(event).to_json()
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def create_user(
    email: str = None,
    first_name: str = None,
    last_name: str = None,
    password: str = None,
) -> None:
    log.info("Walter CLI: Creating user...")
    event = get_create_user_event(email, first_name, last_name, password)
    response = APIRouter.get_method(event).invoke(event).to_json()
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


# STOCKS


@app.command()
def add_stock(token: str = None, stock: str = None, quantity: float = None) -> None:
    log.info("Walter CLI: Adding stock...")
    event = get_add_stock_event(stock, quantity, token)
    response = APIRouter.get_method(event).invoke(event).to_json()
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def get_stock(symbol: str = None) -> None:
    log.info("WalterCLI: GetStock")
    event = get_get_stock_event(symbol)
    response = APIRouter.get_method(event).invoke(event).to_json()
    log.info(f"WalterCLI: GetStock Response:\n{parse_response(response)}")


@app.command()
def delete_stock(token: str = None, stock: str = None) -> None:
    log.info("WalterCLI: DeleteStock")
    event = get_delete_stock_event(stock, token)
    response = APIRouter.get_method(event).invoke(event).to_json()
    log.info(f"WalterCLI: DeleteStock Response:\n{parse_response(response)}")


@app.command()
def get_portfolio(token: str = None) -> None:
    log.info("Walter CLI: Getting portfolio...")
    event = get_portfolio_event(token)
    response = APIRouter.get_method(event).invoke(event).to_json()
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def get_prices(stock: str = None, start_date: str = None, end_date: str = None) -> None:
    log.info("WalterCLI: GetPrices")
    event = get_get_prices_event(stock, start_date, end_date)
    response = APIRouter.get_method(event).invoke(event).to_json()
    log.info(f"WalterCLI: Response:\n{parse_response(response)}")


# CREDIT ACCOUNTS


@app.command()
def create_credit_account(
    token: str = typer.Option(None, help="Authentication token for the user"),
    bank_name: str = typer.Option(None, help="Name of the bank/financial institution"),
    account_name: str = typer.Option(None, help="Display name for the credit account"),
    account_last_four_numbers: str = typer.Option(
        None, help="Last 4 digits of the account number"
    ),
    account_balance: float = typer.Option(
        None, help="Current balance on the credit account"
    ),
) -> None:
    """
    Create a new credit account like a credit card or loan.

    This command allows you to add a credit account to track debts and credit card balances.
    The account will be associated with the authenticated user's profile.

    All fields are required to create a new credit account.
    """
    log.info("WalterCLI: CreateCreditAccount")
    event = get_create_credit_account_event(
        token, bank_name, account_name, account_last_four_numbers, account_balance
    )
    response = APIRouter.get_method(event).invoke(event).to_json()
    log.info(f"WalterCLI: CreateCreditAccount Response:\n{parse_response(response)}")


@app.command()
def get_credit_accounts(
    token: str = typer.Option(None, help="Authentication token for the user")
) -> None:
    """
    Retrieve all credit accounts for the authenticated user.

    This command returns a list of all credit accounts including their balances
    and account details. The accounts must belong to the authenticated user.

    Authentication token is required to access credit account information.
    """
    log.info("WalterCLI: GetCreditAccounts")
    event = get_get_credit_accounts_event(token)
    response = APIRouter.get_method(event).invoke(event).to_json()
    log.info(f"WalterCLI: GetCreditAccounts Response:\n{parse_response(response)}")


@app.command()
def delete_credit_account(
    token: str = typer.Option(None, help="Authentication token for the user"),
    account_id: str = typer.Option(None, help="ID of the credit account to delete"),
) -> None:
    """
    Delete an existing credit account for the authenticated user.

    This command permanently removes a credit account from the user's profile.
    The account must belong to the authenticated user to be deleted.

    Both authentication token and account ID are required to delete an account.
    """
    log.info("WalterCLI: DeleteCreditAccount")
    event = get_delete_credit_account_event(token, account_id)
    response = APIRouter.get_method(event).invoke(event).to_json()
    log.info(f"WalterCLI: DeleteCreditAccount Response:\n{parse_response(response)}")


# CASH ACCOUNTS


@app.command()
def get_cash_accounts(token: str = None) -> None:
    log.info("WalterCLI: GetCashAccounts")
    event = get_get_cash_accounts_event(token)
    response = APIRouter.get_method(event).invoke(event).to_json()
    log.info(f"WalterCLI: GetCashAccounts Response:\n{parse_response(response)}")


@app.command()
def create_cash_account(
    token: str = None,
    bank_name: str = None,
    account_name: str = None,
    account_type: str = None,
    account_last_four_numbers: str = None,
    account_balance: float = None,
) -> None:
    log.info("WalterCLI: CreateCashAccount")
    event = get_create_cash_account_event(
        token,
        bank_name,
        account_name,
        account_type,
        account_last_four_numbers,
        account_balance,
    )
    response = APIRouter.get_method(event).invoke(event).to_json()
    log.info(f"WalterCLI: CreateCashAccount Response:\n{parse_response(response)}")


@app.command()
def update_cash_account(
    token: str = None,
    account_id: str = None,
    bank_name: str = None,
    account_name: str = None,
    account_last_four_numbers: str = None,
    account_balance: float = None,
) -> None:
    log.info("WalterCLI: UpdateCashAccount")
    event = get_update_cash_account_event(
        token,
        account_id,
        bank_name,
        account_name,
        account_last_four_numbers,
        account_balance,
    )
    response = APIRouter.get_method(event).invoke(event).to_json()
    log.info(f"WalterCLI: UpdateCashAccount Response:\n{parse_response(response)}")


@app.command()
def delete_cash_account(
    token: str = None,
    account_id: str = None,
) -> None:
    log.info("WalterCLI: DeleteCashAccount")
    event = get_delete_cash_account_event(
        token,
        account_id,
    )
    response = APIRouter.get_method(event).invoke(event).to_json()
    log.info(f"WalterCLI: UpdateCashAccount Response:\n{parse_response(response)}")


#######################
# INVESTMENT ACCOUNTS #
#######################


@app.command()
def create_investment_account(
    token: str = typer.Option(None, help="Authentication token for the user"),
    bank_name: str = typer.Option(None, help="Name of the bank/financial institution"),
    account_name: str = typer.Option(
        None, help="Display name for the investment account"
    ),
    account_last_four_numbers: str = typer.Option(
        None, help="Last 4 digits of the account number"
    ),
) -> None:
    """
    Create a new investment account for tracking investments and portfolios.

    This command adds an investment account that will be associated with the authenticated user's profile.
    The account can be used to track investments and their performance over time.

    All fields are required to create a new investment account.
    """
    log.info("WalterCLI: CreateInvestmentAccount")
    event = get_create_investment_account_event(
        token, bank_name, account_name, account_last_four_numbers
    )
    response = APIRouter.get_method(event).invoke(event).to_json()
    log.info(
        f"WalterCLI: CreateInvestmentAccount Response:\n{parse_response(response)}"
    )


@app.command()
def get_investment_accounts(
    token: str = typer.Option(None, help="Authentication token for the user")
) -> None:
    """
    Retrieve all investment accounts for the authenticated user.

    This command returns a list of all investment accounts including their details
    and balances. The accounts must belong to the authenticated user.

    Authentication token is required to access investment account information.
    """
    log.info("WalterCLI: GetInvestmentAccounts")
    event = get_get_investment_accounts_event(token)
    response = APIRouter.get_method(event).invoke(event).to_json()
    log.info(f"WalterCLI: GetInvestmentAccounts Response:\n{parse_response(response)}")


@app.command()
def delete_investment_account(
    token: str = typer.Option(None, help="Authentication token for the user"),
    account_id: str = typer.Option(None, help="ID of the investment account to delete"),
) -> None:
    """
    Delete an existing investment account for the authenticated user.

    This command permanently removes an investment account from the user's profile.
    The account must belong to the authenticated user to be deleted.

    Both authentication token and account ID are required to delete an account.
    """
    log.info("WalterCLI: DeleteInvestmentAccount")
    event = get_delete_investment_account_event(token, account_id)
    response = APIRouter.get_method(event).invoke(event).to_json()
    log.info(
        f"WalterCLI: DeleteInvestmentAccount Response:\n{parse_response(response)}"
    )


# TRANSACTIONS


@app.command()
def get_transactions(
    token: str = None, start_date: str = None, end_date: str = None
) -> None:
    log.info("WalterCLI: GetTransactions")
    event = get_get_transactions_event(token, start_date, end_date)
    response = APIRouter.get_method(event).invoke(event).to_json()
    log.info(f"WalterCLI: GetTransactions Response:\n{parse_response(response)}")


@app.command()
def add_transaction(
    token: str = None,
    account_id: str = None,
    date: str = None,
    vendor: str = None,
    amount: float = None,
) -> None:
    log.info("WalterCLI: AddTransaction")
    event = get_add_transaction_event(token, account_id, date, vendor, amount)
    response = APIRouter.get_method(event).invoke(event).to_json()
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
    event = get_edit_transaction_event(
        token, transaction_date, transaction_id, date, vendor, amount, category
    )
    response = APIRouter.get_method(event).invoke(event).to_json()
    log.info(f"WalterCLI: EditTransaction Response:\n{parse_response(response)}")


@app.command()
def delete_transaction(
    token: str = None, date: str = None, transaction_id: str = None
) -> None:
    log.info("WalterCLI: DeleteTransaction")
    event = get_delete_transaction_event(token, date, transaction_id)
    response = APIRouter.get_method(event).invoke(event).to_json()
    log.info(f"WalterCLI: DeleteTransaction Response:\n{parse_response(response)}")


# PLAID


@app.command()
def create_link_token(token: str = None) -> None:
    log.info("WalterCLI: CreateLinkToken")
    event = get_create_link_token_event(token)
    response = APIRouter.get_method(event).invoke(event).to_json()
    log.info(f"WalterCLI: CreateLinkToken Response:\n{parse_response(response)}")


@app.command()
def exchange_public_token(
    token: str = None,
    public_token: str = None,
    institution_id: str = None,
    institution_name: str = None,
) -> None:
    log.info("WalterCLI: ExchangePublicToken")
    event = get_exchange_public_token_event(
        token, public_token, institution_id, institution_name, []
    )
    response = APIRouter.get_method(event).invoke(event).to_json()
    log.info(f"WalterCLI: ExchangePublicToken Response:\n{parse_response(response)}")


@app.command()
def sync_transactions(access_token: str = None, webhook_code: str = None) -> None:
    log.info("WalterCLI: SyncTransactions")
    event = get_sync_transactions_event(access_token, webhook_code)
    response = APIRouter.get_method(event).invoke(event).to_json()
    log.info(f"WalterCLI: SyncTransactions Response:\n{parse_response(response)}")


###################
# WALTER CANARIES #
###################


@app.command()
def auth_user_canary() -> None:
    log.info("WalterCLI: AuthUserCanary...")
    response = CanaryRouter.get_canary(event={"canary": "auth_user"}).invoke()
    log.info(f"WalterCLI: AuthUserCanary Response:\n{parse_response(response)}")


@app.command()
def get_transactions_canary() -> None:
    log.info("WalterCLI: GetTransactionsCanary")
    response = CanaryRouter.get_canary(event={"canary": "get_transactions"}).invoke()
    log.info(f"WalterCLI: GetTransactionsCanary Response:\n{parse_response(response)}")


@app.command()
def get_user_canary() -> None:
    log.info("WalterCLI: GetUserCanary...")
    response = CanaryRouter.get_canary(event={"canary": "get_user"}).invoke()
    log.info(f"WalterCLI: GetUserCanary Response:\n{parse_response(response)}")


@app.command()
def get_stock_canary() -> None:
    log.info("WalterCLI: GetStockCanary...")
    response = CanaryRouter.get_canary(event={"canary": "get_stock"}).invoke()
    log.info(f"WalterCLI: GetStockCanary Response:\n{parse_response(response)}")


@app.command()
def get_portfolio_canary() -> None:
    log.info("WalterCLI: GetPortfolioCanary...")
    response = CanaryRouter.get_canary(event={"canary": "get_portfolio"}).invoke()
    log.info(f"WalterCLI: GetPortfolioCanary Response:\n{parse_response(response)}")


@app.command()
def get_prices_canary() -> None:
    log.info("WalterCLI: GetPricesCanary...")
    response = CanaryRouter.get_canary(event={"canary": "get_prices"}).invoke()
    log.info(f"WalterCLI: GetPricesCanary Response:\n{parse_response(response)}")


if __name__ == "__main__":
    app()
