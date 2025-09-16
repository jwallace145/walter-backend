from typing import List, Optional, Tuple

import pytest

from src.api.common.exceptions import InvalidPlaidInstitution
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Response, Status
from src.api.factory import APIMethod, APIMethodFactory
from src.api.plaid.exchange_public_token.method import ExchangePublicToken
from src.api.plaid.exchange_public_token.models import AccountDetails
from src.api.routing.methods import HTTPMethod
from src.auth.authenticator import WalterAuthenticator
from src.auth.models import Tokens
from src.database.accounts.models import Account
from src.database.client import WalterDB
from src.database.sessions.models import Session
from src.database.users.models import User
from src.plaid.models import ExchangePublicTokenResponse
from tst.api.utils import UNIT_TEST_REQUEST_ID, get_api_event


@pytest.fixture
def exchange_public_token_api(
    api_method_factory: APIMethodFactory,
) -> WalterAPIMethod:
    return api_method_factory.get_api(
        APIMethod.EXCHANGE_PUBLIC_TOKEN, UNIT_TEST_REQUEST_ID
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


def test_exchange_public_token_success(
    exchange_public_token_api: ExchangePublicToken,
    walter_authenticator: WalterAuthenticator,
    walter_db: WalterDB,
) -> None:
    user_id = "user-001"
    session_id = "session-001"
    token, expiry = walter_authenticator.generate_access_token(user_id, session_id)
    event: dict = get_api_event(
        path="/plaid/exchange_public_token",
        http_method=HTTPMethod.POST,
        token=token,
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
    session: Optional[Session] = walter_db.get_session(user_id, session_id)
    assert session is not None
    response: Response = exchange_public_token_api.execute(event, session)
    assert response.api_name == ExchangePublicToken.API_NAME
    assert response.http_status == HTTPStatus.OK
    assert response.status == Status.SUCCESS
    assert response.data is not None
    data = response.data
    assert data["institution_id"] == "fake-institution-id"
    assert data["institution_name"] == "Fake Institution"
    assert data["num_accounts"] == 1


def test_get_institution_details_too_many_institutions_failure(
    exchange_public_token_api: ExchangePublicToken,
    walter_authenticator: WalterAuthenticator,
    walter_db: WalterDB,
) -> None:
    account_details: List[AccountDetails] = [
        AccountDetails(
            institution_id="fake-institution-id-1",
            institution_name="Fake Institution 1",
            account_id="fake-account-id",
            account_name="Fake Account",
            account_type="credit",
            account_subtype="credit card",
            account_last_four_numbers="1234",
        ),
        AccountDetails(
            institution_id="fake-institution-id-2",
            institution_name="Fake Institution 1",
            account_id="fake-account-id",
            account_name="Fake Account",
            account_type="credit",
            account_subtype="credit card",
            account_last_four_numbers="1234",
        ),
    ]
    with pytest.raises(InvalidPlaidInstitution):
        exchange_public_token_api._get_institution_details(account_details)
