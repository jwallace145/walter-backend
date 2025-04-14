import json

import typer

from src.utils.log import Logger
from tst.api.utils import (
    get_auth_user_event,
    get_create_user_event,
    get_get_user_event,
    get_add_stock_event,
    get_portfolio_event,
    get_send_newsletter_event,
    get_send_verify_email_event,
    get_verify_email_event,
    get_change_password_event,
    get_send_change_password_email_event,
    get_get_stock_event,
    get_unsubscribe_event,
    get_subscribe_event,
    get_news_summary_event,
    get_get_prices_event,
    get_search_stocks_event,
    get_verify_purchase_newsletter_subscription_event,
    get_purchase_newsletter_subscription_event,
    get_get_newsletter_event,
    get_add_expense_event,
    get_get_expenses_event,
    get_delete_expense_event,
)
from tst.events.utils import (
    get_walter_backend_event,
    get_create_news_summary_and_archive_event,
)
from walter import (
    auth_user_entrypoint,
    create_user_entrypoint,
    get_user_entrypoint,
    add_stock_entrypoint,
    get_portfolio_entrypoint,
    send_newsletter_entrypoint,
    create_newsletter_and_send_entrypoint,
    send_verify_email_entrypoint,
    verify_email_entrypoint,
    change_password_entrypoint,
    send_change_password_email_entrypoint,
    get_stock_entrypoint,
    unsubscribe_entrypoint,
    subscribe_entrypoint,
    get_news_summary_entrypoint,
    get_prices_entrypoint,
    search_stocks_entrypoint,
    add_newsletter_requests_entrypoint,
    add_news_summary_requests_entrypoint,
    create_news_summary_and_archive_entrypoint,
    purchase_newsletter_subscription_entrypoint,
    verify_purchase_newsletter_subscription_entrypoint,
    get_newsletters_entrypoint,
    get_newsletter_entrypoint,
    get_statistics_entrypoint,
    auth_user_canary_entrypoint,
    get_user_canary_entrypoint,
    get_portfolio_canary_entrypoint,
    get_prices_canary_entrypoint,
    get_news_summary_canary_entrypoint,
    get_stock_canary_entrypoint,
    search_stocks_canary_entrypoint,
    add_expense_entrypoint,
    get_expenses_entrypoint,
    delete_expense_entrypoint,
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

##############
# WALTER API #
##############


@app.command()
def auth_user(email: str = None, password: str = None) -> None:
    log.info("Walter CLI: Authenticating user...")
    event = get_auth_user_event(email, password)
    response = auth_user_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def create_user(email: str = None, username: str = None, password: str = None) -> None:
    log.info("Walter CLI: Creating user...")
    event = get_create_user_event(email, username, password)
    response = create_user_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def get_user(token: str = None) -> None:
    log.info("Walter CLI: Getting user...")
    event = get_get_user_event(token)
    response = get_user_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def add_stock(token: str = None, stock: str = None, quantity: float = None) -> None:
    log.info("Walter CLI: Adding stock...")
    event = get_add_stock_event(stock, quantity, token)
    response = add_stock_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def get_stock(symbol: str = None) -> None:
    log.info("WalterCLI: GetStock")
    event = get_get_stock_event(symbol)
    response = get_stock_entrypoint(event, CONTEXT)
    log.info(f"WalterCLI: GetStock Response:\n{parse_response(response)}")


@app.command()
def get_statistics(symbol: str = None) -> None:
    log.info("WalterCLI: GetStatistics")
    event = get_get_stock_event(symbol)
    response = get_statistics_entrypoint(event, CONTEXT)
    log.info(f"WalterCLI: GetStatistics Response:\n{parse_response(response)}")


@app.command()
def get_prices(stock: str = None) -> None:
    log.info("WalterCLI: GetPrices")
    event = get_get_prices_event(stock)
    response = get_prices_entrypoint(event, CONTEXT)
    log.info(f"WalterCLI: Response:\n{parse_response(response)}")


@app.command()
def get_portfolio(token: str = None) -> None:
    log.info("Walter CLI: Getting portfolio...")
    event = get_portfolio_event(token)
    response = get_portfolio_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def get_news_summary(stock: str = None) -> None:
    log.info("WalterCLI: GetNewsSummary...")
    event = get_news_summary_event(stock)
    response = get_news_summary_entrypoint(event, CONTEXT)
    log.info(f"WalterCLI: GetNewsSummary Response:\n{parse_response(response)}")


@app.command()
def send_newsletter(token: str = None) -> None:
    log.info("Walter CLI: Sending newsletter...")
    event = get_send_newsletter_event(token)
    response = send_newsletter_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def get_newsletter(token: str = None, date: str = None) -> None:
    log.info("WalterCLI: GetNewsletter")
    event = get_get_newsletter_event(token, date)
    response = get_newsletter_entrypoint(event, CONTEXT)
    log.info(f"WalterCLI: GetNewsletter Response:\n{parse_response(response)}")


@app.command()
def get_newsletters(token: str = None, page: int = None) -> None:
    log.info("WalterCLI: GetNewsletters")
    event = get_send_newsletter_event(token, page)
    response = get_newsletters_entrypoint(event, CONTEXT)
    log.info(f"WalterCLI: GetNewsletters Response:\n{parse_response(response)}")


@app.command()
def verify_email(token: str = None) -> None:
    log.info("Walter CLI: Verifying email...")
    event = get_verify_email_event(token)
    response = verify_email_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def send_verify_email(token: str = None) -> None:
    log.info("Walter CLI: Sending verify email...")
    event = get_send_verify_email_event(token)
    response = send_verify_email_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def change_password(token: str = None, new_password: str = None) -> None:
    log.info("Walter CLI: Changing password...")
    event = get_change_password_event(token, new_password)
    response = change_password_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def send_change_password_email(email: str = None) -> None:
    log.info("Walter CLI: Sending change password email...")
    event = get_send_change_password_email_event(email)
    response = send_change_password_email_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def subscribe(token: str = None) -> None:
    log.info("Walter CLI: Subscribing user from newsletter...")
    event = get_subscribe_event(token)
    response = subscribe_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def unsubscribe(token: str = None) -> None:
    log.info("Walter CLI: Unsubscribing user from newsletter...")
    event = get_unsubscribe_event(token)
    response = unsubscribe_entrypoint(event, CONTEXT)
    log.info(f"Walter CLI: Response:\n{parse_response(response)}")


@app.command()
def search_stocks(stock: str = None) -> None:
    log.info("WalterCLI: SearchStocks")
    event = get_search_stocks_event(stock)
    response = search_stocks_entrypoint(event, CONTEXT)
    log.info(f"WalterCLI: SearchStocks Response:\n{parse_response(response)}")


@app.command()
def purchase_newsletter_subscription(token: str = None) -> None:
    log.info("WalterCLI: PurchaseNewsletterSubscription")
    event = get_purchase_newsletter_subscription_event(token)
    response = purchase_newsletter_subscription_entrypoint(event, CONTEXT)
    log.info(
        f"WalterCLI: PurchaseNewsletterSubscription Response:\n{parse_response(response)}"
    )


@app.command()
def verify_purchase_newsletter_subscription(
    token: str = None, session_id: str = None
) -> None:
    log.info("WalterCLI: VerifyPurchaseNewsletterSubscription")
    event = get_verify_purchase_newsletter_subscription_event(token, session_id)
    response = verify_purchase_newsletter_subscription_entrypoint(event, CONTEXT)
    log.info(
        f"WalterCLI: VerifyPurchaseNewsletterSubscription Response:\n{parse_response(response)}"
    )


@app.command()
def add_expense(
    token: str = None,
    date: str = None,
    vendor: str = None,
    amount: float = None,
    category: str = None,
) -> None:
    log.info("WalterCLI: AddExpense")
    event = get_add_expense_event(token, date, vendor, amount, category)
    response = add_expense_entrypoint(event, CONTEXT)
    log.info(f"WalterCLI: AddExpense Response:\n{parse_response(response)}")


@app.command()
def get_expenses(
    token: str = None, start_date: str = None, end_date: str = None
) -> None:
    log.info("WalterCLI: GetExpenses")
    event = get_get_expenses_event(token, start_date, end_date)
    response = get_expenses_entrypoint(event, CONTEXT)
    log.info(f"WalterCLI: GetExpenses Response:\n{parse_response(response)}")


@app.command()
def delete_expense(token: str = None, date: str = None, expense_id: str = None) -> None:
    log.info("WalterCLI: DeleteExpense")
    event = get_delete_expense_event(token, date, expense_id)
    response = delete_expense_entrypoint(event, CONTEXT)
    log.info(f"WalterCLI: DeleteExpense Response:\n{parse_response(response)}")


###################
# WALTER CANARIES #
###################


@app.command()
def auth_user_canary() -> None:
    log.info("WalterCLI: AuthUserCanary...")
    response = auth_user_canary_entrypoint({}, CONTEXT)
    log.info(f"WalterCLI: AuthUserCanary Response:\n{parse_response(response)}")


@app.command()
def get_user_canary() -> None:
    log.info("WalterCLI: GetUserCanary...")
    response = get_user_canary_entrypoint({}, CONTEXT)
    log.info(f"WalterCLI: GetUserCanary Response:\n{parse_response(response)}")


@app.command()
def get_stock_canary() -> None:
    log.info("WalterCLI: GetStockCanary...")
    response = get_stock_canary_entrypoint({}, CONTEXT)
    log.info(f"WalterCLI: GetStockCanary Response:\n{parse_response(response)}")


@app.command()
def get_portfolio_canary() -> None:
    log.info("WalterCLI: GetPortfolioCanary...")
    response = get_portfolio_canary_entrypoint({}, CONTEXT)
    log.info(f"WalterCLI: GetPortfolioCanary Response:\n{parse_response(response)}")


@app.command()
def get_prices_canary() -> None:
    log.info("WalterCLI: GetPricesCanary...")
    response = get_prices_canary_entrypoint({}, CONTEXT)
    log.info(f"WalterCLI: GetPricesCanary Response:\n{parse_response(response)}")


@app.command()
def get_news_summary_canary() -> None:
    log.info("WalterCLI: GetNewsSummaryCanary...")
    response = get_news_summary_canary_entrypoint({}, CONTEXT)
    log.info(f"WalterCLI: GetNewsSummaryCanary Response:\n{parse_response(response)}")


@app.command()
def search_stocks_canary() -> None:
    log.info("WalterCLI: SearchStocksCanary")
    response = search_stocks_canary_entrypoint({}, CONTEXT)
    log.info(f"WalterCLI: SearchStocksCanary Response:\n{parse_response(response)}")


####################
# WALTER WORKFLOWS #
####################


@app.command()
def send_newsletters():
    log.info("WalterCLI: AddNewsletterRequests")
    response = add_newsletter_requests_entrypoint({}, CONTEXT)
    log.info(f"WalterCLI: Response:\n{parse_response(response)}")


@app.command()
def create_and_send_newsletter(email: str = None) -> None:
    log.info("WalterCLI: CreateNewsletterAndSend")
    event = get_walter_backend_event(email)
    response = create_newsletter_and_send_entrypoint(event, CONTEXT)
    log.info(f"WalterCLI: Response:\n{parse_response(response)}")


@app.command()
def create_news_summaries() -> None:
    log.info("WalterCLI: AddNewsSummaryRequests")
    response = add_news_summary_requests_entrypoint({}, CONTEXT)
    log.info(f"WalterCLI: Response:\n{parse_response(response)}")


@app.command()
def create_news_summary_and_archive(stock: str = None, datestamp: str = None) -> None:
    log.info("WalterCLI: CreateNewsSummaryAndArchive")
    event = get_create_news_summary_and_archive_event(stock, datestamp)
    response = create_news_summary_and_archive_entrypoint(event, CONTEXT)
    log.info(f"WalterCLI: Response:\n{parse_response(response)}")


if __name__ == "__main__":
    app()
