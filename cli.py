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
    get_create_link_token_event,
    get_exchange_public_token_event,
    get_sync_transactions_event,
    get_delete_stock_event,
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


# ACCOUNTS

# TODO: Add accounts CLI commands

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
