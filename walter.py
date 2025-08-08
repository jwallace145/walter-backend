from src.api.add_stock import AddStock
from src.api.delete_stock import DeleteStock
from src.api.get_portfolio import GetPortfolio
from src.api.get_prices import GetPrices
from src.api.get_stock import GetStock
from src.api.plaid.create_link_token import CreateLinkToken
from src.api.plaid.exchange_public_token import ExchangePublicToken
from src.api.plaid.refresh_transactions import RefreshTransactions
from src.api.plaid.sync_transactions import SyncTransactions
from src.api.routing.router import APIRouter
from src.canaries.auth_user import AuthUserCanary
from src.canaries.get_news_summary import GetNewsSummaryCanary
from src.canaries.get_newsletters import GetNewslettersCanary
from src.canaries.get_portfolio import GetPortfolioCanary
from src.canaries.get_prices import GetPricesCanary
from src.canaries.get_stock import GetStockCanary
from src.canaries.get_transactions import GetTransactionsCanary
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
    plaid,
    sync_user_transactions_queue,
)
from src.workflows.add_news_summary_requests import (
    AddNewsSummaryRequests,
)
from src.workflows.add_newsletter_requests import AddNewsletterRequests
from src.workflows.create_news_summary_and_archive import CreateNewsSummaryAndArchive
from src.workflows.create_newsletter_and_send import (
    CreateNewsletterAndSend,
)
from src.workflows.sync_user_transactions import SyncUserTransactions


##############
# WALTER API #
##############


def walter_api_entrypoint(event, context) -> dict:
    return APIRouter.get_method(event).invoke(event).to_json()


def get_stock_entrypoint(event, context) -> dict:
    return (
        GetStock(walter_authenticator, walter_cw, walter_db, walter_stocks_api)
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


def get_prices_entrypoint(event, context) -> dict:
    return (
        GetPrices(walter_authenticator, walter_cw, walter_db, walter_stocks_api)
        .invoke(event)
        .to_json()
    )


def create_link_token_entrypoint(event, context) -> dict:
    return (
        CreateLinkToken(walter_authenticator, walter_cw, walter_db, plaid)
        .invoke(event)
        .to_json()
    )


def exchange_public_token_entrypoint(event, context) -> dict:
    return (
        ExchangePublicToken(
            walter_authenticator,
            walter_cw,
            walter_db,
            plaid,
            sync_user_transactions_queue,
        )
        .invoke(event)
        .to_json()
    )


def sync_transactions_entrypoint(event, context) -> dict:
    return (
        SyncTransactions(
            walter_authenticator,
            walter_cw,
            walter_db,
            sync_user_transactions_queue,
        )
        .invoke(event)
        .to_json()
    )


def refresh_transactions_entrypoint(event, context) -> dict:
    return (
        RefreshTransactions(walter_authenticator, walter_cw, walter_db, plaid)
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


def sync_user_transactions_entrypoint(event, context) -> dict:
    return SyncUserTransactions(walter_event_parser, plaid, walter_db).invoke(event)


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
