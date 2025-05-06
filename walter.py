from src.api.transactions.add_transaction import AddTransaction
from src.api.add_stock import AddStock
from src.api.auth_user import AuthUser
from src.api.change_password import ChangePassword
from src.api.create_cash_account import CreateCashAccount
from src.api.create_user import CreateUser
from src.api.delete_cash_account import DeleteCashAccount
from src.api.delete_stock import DeleteStock
from src.api.transactions.delete_transaction import DeleteTransaction
from src.api.transactions.edit_transaction import EditTransaction
from src.api.get_cash_accounts import GetCashAccounts
from src.api.get_news_summary import GetNewsSummary
from src.api.get_newsletter import GetNewsletter
from src.api.get_newsletters import GetNewsletters
from src.api.get_portfolio import GetPortfolio
from src.api.get_prices import GetPrices
from src.api.get_statistics import GetStatistics
from src.api.get_stock import GetStock
from src.api.transactions.get_transactions import GetTransactions
from src.api.get_user import GetUser
from src.api.purchase_newsletter_subscription import PurchaseNewsletterSubscription
from src.api.search_stocks import SearchStocks
from src.api.send_change_password_email import SendChangePasswordEmail
from src.api.send_newsletter import SendNewsletter
from src.api.send_verify_email import SendVerifyEmail
from src.api.subscribe import Subscribe
from src.api.unsubscribe import Unsubscribe
from src.api.update_cash_account import UpdateCashAccount
from src.api.update_password import UpdatePassword
from src.api.update_user import UpdateUser
from src.api.verify_email import VerifyEmail
from src.api.verify_purchase_newsletter_subscription import (
    VerifyPurchaseNewsletterSubscription,
)
from src.canaries.auth_user import AuthUserCanary
from src.canaries.get_transactions import GetTransactionsCanary
from src.canaries.get_news_summary import GetNewsSummaryCanary
from src.canaries.get_newsletters import GetNewslettersCanary
from src.canaries.get_portfolio import GetPortfolioCanary
from src.canaries.get_prices import GetPricesCanary
from src.canaries.get_stock import GetStockCanary
from src.canaries.get_user import GetUserCanary
from src.canaries.search_stocks import SearchStocksCanary
from src.clients import (
    walter_cw,
    walter_db,
    walter_sm,
    walter_stocks_api,
    newsletters_queue,
    walter_authenticator,
    template_engine,
    templates_bucket,
    walter_ses,
    news_summaries_bucket,
    news_summaries_queue,
    walter_event_parser,
    walter_news_summary_client,
    walter_ai,
    newsletters_bucket,
    walter_payments,
    expense_categorizer,
    s3,
)
from src.workflows.add_news_summary_requests import (
    AddNewsSummaryRequests,
)
from src.workflows.add_newsletter_requests import AddNewsletterRequests
from src.workflows.create_news_summary_and_archive import CreateNewsSummaryAndArchive
from src.workflows.create_newsletter_and_send import (
    CreateNewsletterAndSend,
)


##############
# WALTER API #
##############


def create_user_entrypoint(event, context) -> dict:
    return (
        CreateUser(
            walter_authenticator,
            walter_cw,
            walter_db,
            walter_ses,
            template_engine,
            templates_bucket,
        )
        .invoke(event)
        .to_json()
    )


def auth_user_entrypoint(event, context) -> dict:
    return (
        AuthUser(walter_authenticator, walter_cw, walter_db, walter_sm)
        .invoke(event)
        .to_json()
    )


def get_user_entrypoint(event, context) -> dict:
    return (
        GetUser(walter_authenticator, walter_cw, walter_db, walter_sm, s3)
        .invoke(event)
        .to_json()
    )


def update_user_entrypoint(event, context) -> dict:
    return (
        UpdateUser(walter_authenticator, walter_cw, walter_db, s3)
        .invoke(event)
        .to_json()
    )


def get_stock_entrypoint(event, context) -> dict:
    return (
        GetStock(walter_authenticator, walter_cw, walter_db, walter_stocks_api)
        .invoke(event)
        .to_json()
    )


def get_statistics_entrypoint(event, context) -> dict:
    return (
        GetStatistics(walter_authenticator, walter_cw, walter_stocks_api)
        .invoke(event)
        .to_json()
    )


def add_stock_entrypoint(event, context) -> dict:
    return (
        AddStock(
            walter_authenticator, walter_cw, walter_db, walter_stocks_api, walter_sm
        )
        .invoke(event)
        .to_json()
    )


def delete_stock_entrypoint(event, context) -> dict:
    return (
        DeleteStock(
            walter_authenticator, walter_cw, walter_db, walter_stocks_api, walter_sm
        )
        .invoke(event)
        .to_json()
    )


def get_portfolio_entrypoint(event, context) -> dict:
    return (
        GetPortfolio(
            walter_authenticator, walter_cw, walter_db, walter_sm, walter_stocks_api
        )
        .invoke(event)
        .to_json()
    )


def get_news_summary_entrypoint(event, context) -> dict:
    return (
        GetNewsSummary(
            walter_authenticator,
            walter_cw,
            walter_db,
            walter_stocks_api,
            news_summaries_bucket,
            news_summaries_queue,
        )
        .invoke(event)
        .to_json()
    )


def send_newsletter_entrypoint(event, context) -> dict:
    return (
        SendNewsletter(
            walter_authenticator, walter_cw, walter_db, newsletters_queue, walter_sm
        )
        .invoke(event)
        .to_json()
    )


def get_newsletter_entrypoint(event, context) -> dict:
    return (
        GetNewsletter(walter_authenticator, walter_cw, walter_db, newsletters_bucket)
        .invoke(event)
        .to_json()
    )


def get_newsletters_entrypoint(event, context) -> dict:
    return (
        GetNewsletters(walter_authenticator, walter_cw, walter_db, newsletters_bucket)
        .invoke(event)
        .to_json()
    )


def get_prices_entrypoint(event, context) -> dict:
    return (
        GetPrices(walter_authenticator, walter_cw, walter_db, walter_stocks_api)
        .invoke(event)
        .to_json()
    )


def verify_email_entrypoint(event, context) -> dict:
    return (
        VerifyEmail(walter_authenticator, walter_cw, walter_db).invoke(event).to_json()
    )


def send_verify_email_entrypoint(event, context) -> dict:
    return (
        SendVerifyEmail(
            walter_authenticator,
            walter_cw,
            walter_db,
            walter_ses,
            template_engine,
            templates_bucket,
        )
        .invoke(event)
        .to_json()
    )


def change_password_entrypoint(event, context) -> dict:
    return (
        ChangePassword(walter_authenticator, walter_cw, walter_db)
        .invoke(event)
        .to_json()
    )


def update_password_entrypoint(event, context) -> dict:
    return (
        UpdatePassword(walter_authenticator, walter_cw, walter_db)
        .invoke(event)
        .to_json()
    )


def send_change_password_email_entrypoint(event, context) -> dict:
    return (
        SendChangePasswordEmail(
            walter_authenticator,
            walter_cw,
            walter_db,
            walter_ses,
            template_engine,
            templates_bucket,
        )
        .invoke(event)
        .to_json()
    )


def subscribe_entrypoint(event, context) -> dict:
    return Subscribe(walter_authenticator, walter_cw, walter_db).invoke(event).to_json()


def unsubscribe_entrypoint(event, context) -> dict:
    return (
        Unsubscribe(walter_authenticator, walter_cw, walter_db, walter_sm)
        .invoke(event)
        .to_json()
    )


def search_stocks_entrypoint(event, context) -> dict:
    return (
        SearchStocks(walter_authenticator, walter_cw, walter_stocks_api)
        .invoke(event)
        .to_json()
    )


def purchase_newsletter_subscription_entrypoint(event, context) -> dict:
    return (
        PurchaseNewsletterSubscription(
            walter_authenticator, walter_cw, walter_db, walter_sm, walter_payments
        )
        .invoke(event)
        .to_json()
    )


def verify_purchase_newsletter_subscription_entrypoint(event, context) -> dict:
    return (
        VerifyPurchaseNewsletterSubscription(
            walter_authenticator, walter_cw, walter_db, walter_sm, walter_payments
        )
        .invoke(event)
        .to_json()
    )


def add_transaction_entrypoint(event, context) -> dict:
    return (
        AddTransaction(walter_authenticator, walter_cw, walter_db, expense_categorizer)
        .invoke(event)
        .to_json()
    )


def edit_transaction_entrypoint(event, context) -> dict:
    return (
        EditTransaction(walter_authenticator, walter_cw, walter_db)
        .invoke(event)
        .to_json()
    )


def get_transactions_entrypoint(event, context) -> dict:
    return (
        GetTransactions(walter_authenticator, walter_cw, walter_db)
        .invoke(event)
        .to_json()
    )


def delete_transaction_entrypoint(event, context) -> dict:
    return (
        DeleteTransaction(walter_authenticator, walter_cw, walter_db)
        .invoke(event)
        .to_json()
    )


def get_cash_accounts_entrypoint(event, context) -> dict:
    return (
        GetCashAccounts(walter_authenticator, walter_cw, walter_db)
        .invoke(event)
        .to_json()
    )


def create_cash_account_entrypoint(event, context) -> dict:
    return (
        CreateCashAccount(walter_authenticator, walter_cw, walter_db)
        .invoke(event)
        .to_json()
    )


def update_cash_account_entrypoint(event, context) -> dict:
    return (
        UpdateCashAccount(walter_authenticator, walter_cw, walter_db)
        .invoke(event)
        .to_json()
    )


def delete_cash_account_entrypoint(event, context) -> dict:
    return (
        DeleteCashAccount(walter_authenticator, walter_cw, walter_db)
        .invoke(event)
        .to_json()
    )


###################
# WALTER CANARIES #
###################


def auth_user_canary_entrypoint(event, context) -> dict:
    return AuthUserCanary(walter_cw).invoke()


def get_transactions_canary_entrypoint(event, context) -> dict:
    return GetTransactionsCanary(walter_authenticator, walter_cw).invoke()


def get_user_canary_entrypoint(event, context) -> dict:
    return GetUserCanary(walter_authenticator, walter_cw).invoke()


def get_stock_canary_entrypoint(event, context) -> dict:
    return GetStockCanary(walter_cw).invoke()


def get_portfolio_canary_entrypoint(event, context) -> dict:
    return GetPortfolioCanary(walter_authenticator, walter_cw).invoke()


def get_prices_canary_entrypoint(event, context) -> dict:
    return GetPricesCanary(walter_cw).invoke()


def get_news_summary_canary_entrypoint(event, context) -> dict:
    return GetNewsSummaryCanary(walter_cw).invoke()


def get_newsletters_canary_entrypoint(event, context) -> dict:
    return GetNewslettersCanary(walter_authenticator, walter_cw).invoke()


def search_stocks_canary_entrypoint(event, context) -> dict:
    return SearchStocksCanary(walter_cw).invoke()


####################
# WALTER WORKFLOWS #
####################


def add_newsletter_requests_entrypoint(event, context) -> dict:
    return AddNewsletterRequests(walter_db, newsletters_queue, walter_cw).invoke(event)


def create_newsletter_and_send_entrypoint(event, context) -> dict:
    return CreateNewsletterAndSend(
        walter_authenticator,
        walter_event_parser,
        walter_db,
        walter_stocks_api,
        walter_ai,
        walter_ses,
        walter_cw,
        template_engine,
        templates_bucket,
        news_summaries_bucket,
        newsletters_bucket,
        newsletters_queue,
    ).invoke(event)


def add_news_summary_requests_entrypoint(event, context) -> dict:
    return AddNewsSummaryRequests(walter_db, news_summaries_queue, walter_cw).invoke(
        event
    )


def create_news_summary_and_archive_entrypoint(event, context) -> dict:
    return CreateNewsSummaryAndArchive(
        walter_event_parser,
        walter_db,
        walter_stocks_api,
        walter_news_summary_client,
        news_summaries_bucket,
        news_summaries_queue,
        walter_cw,
    ).invoke(event)
