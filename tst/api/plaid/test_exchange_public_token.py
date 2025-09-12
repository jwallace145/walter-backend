from typing import List, Tuple

import pytest

from src.api.plaid.exchange_public_token.method import ExchangePublicToken
from src.api.plaid.exchange_public_token.models import AccountDetails
from src.api.routing.methods import HTTPMethod
from src.auth.authenticator import WalterAuthenticator
from src.auth.models import Tokens
from src.database.accounts.models import Account
from src.database.client import WalterDB
from src.database.users.models import User
from src.environment import Domain
from src.metrics.client import DatadogMetricsClient
from src.plaid.models import ExchangePublicTokenResponse
from src.transactions.queue import SyncUserTransactionsTaskQueue
from tst.api.utils import get_api_event
from tst.plaid.mock import MockPlaidClient


@pytest.fixture
def exchange_public_token_api(
    walter_authenticator: WalterAuthenticator,
    datadog_metrics: DatadogMetricsClient,
    walter_db: WalterDB,
    plaid_client: MockPlaidClient,
    sync_transactions_task_queue: SyncUserTransactionsTaskQueue = None,
) -> ExchangePublicToken:
    return ExchangePublicToken(
        Domain.TESTING,
        walter_authenticator,
        datadog_metrics,
        walter_db,
        plaid_client,
        sync_transactions_task_queue,
    )


def test_get_details_from_event_success(
    exchange_public_token_api: ExchangePublicToken,
    walter_authenticator: WalterAuthenticator,
) -> None:
    user_id = "user-001"
    tokens = walter_authenticator.generate_tokens(user_id)
    event = get_api_event(
        path="/plaid/exchange_public_token",
        http_method=HTTPMethod.POST,
        token=tokens.access_token,
        body={
            "public_token": "fake-public-token",
            "institution_id": "fake-institution-id",
            "institution_name": "Fake Institution",
            "accounts": [
                {
                    "account_id": "fake-account-id",
                    "account_name": "Fake Account",
                    "account_type": "fake-account-type",
                    "account_subtype": "fake-account-subtype",
                    "account_last_four_numbers": "1234",
                }
            ],
        },
    )
    response: Tuple[str, List[AccountDetails]] = (
        exchange_public_token_api._get_details_from_event(event)
    )
    assert isinstance(response[0], str)
    assert isinstance(response[1], list)
    assert len(response[1]) == 1
    assert isinstance(response[1][0], AccountDetails)
    assert response[1][0].account_id == "fake-account-id"
    assert response[1][0].account_name == "Fake Account"
    assert response[1][0].account_type == "fake-account-type"
    assert response[1][0].account_subtype == "fake-account-subtype"
    assert response[1][0].account_last_four_numbers == "1234"


def test_save_accounts_success(
    exchange_public_token_api: ExchangePublicToken,
    walter_authenticator: WalterAuthenticator,
    walter_db: WalterDB,
) -> None:
    user_id = "user-001"
    tokens: Tokens = walter_authenticator.generate_tokens(user_id)
    event: dict = get_api_event(
        path="/plaid/exchange_public_token",
        http_method=HTTPMethod.POST,
        token=tokens.access_token,
        body={
            "public_token": "fake-public-token",
            "institution_id": "fake-institution-id",
            "institution_name": "Fake Institution",
            "accounts": [
                {
                    "account_id": "fake-account-id",
                    "account_name": "Fake Account",
                    "account_type": "credit",
                    "account_subtype": "credit card",
                    "account_last_four_numbers": "1234",
                }
            ],
        },
    )
    user: User = walter_db.get_user_by_id(user_id)
    exchange_details: Tuple[str, List[AccountDetails]] = (
        exchange_public_token_api._get_details_from_event(event)
    )
    public_token, plaid_accounts = exchange_details
    exchange_response: ExchangePublicTokenResponse = (
        exchange_public_token_api._exchange_token(public_token)
    )
    accounts: List[Account] = exchange_public_token_api._save_accounts(
        exchange_response, user, plaid_accounts
    )
    assert len(accounts) == 1
    assert isinstance(accounts[0], Account)
    assert accounts[0].user_id == user_id
    assert accounts[0].plaid_account_id == "fake-account-id"
    assert walter_db.get_account_by_plaid_account_id("fake-account-id") is not None
