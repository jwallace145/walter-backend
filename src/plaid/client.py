import datetime as dt
from dataclasses import dataclass
from typing import Optional

from plaid import ApiClient, Configuration
from plaid.api.plaid_api import PlaidApi
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import \
    ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import \
    LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.transactions_refresh_request import TransactionsRefreshRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from src.database.transactions.models import Transaction
from src.plaid.models import (CreateLinkTokenResponse,
                              ExchangePublicTokenResponse,
                              SyncTransactionsResponse)
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class PlaidClient:
    """
    Plaid Client
    """

    CLIENT_NAME = "WalterAI"
    REDIRECT_URI = "http://localhost:3000/"  # TODO: Fix me!
    WEBHOOK_URL = "https://084slq55lk.execute-api.us-east-1.amazonaws.com/dev/plaid/sync-transactions"  # TODO: Fix me! this is hardcoded to point at WalterAPI-dev!

    client_id: str
    secret: str
    environment: str

    # all the default none fields set during post-int
    configuration: Configuration = None
    api_client: ApiClient = None
    client: PlaidApi = None

    def __post_init__(self) -> None:
        log.debug(
            f"Initializing '{self.environment}' Plaid client with client ID: '{self.client_id}'"
        )
        self.configuration = self._get_configuration()
        self.api_client = ApiClient(self.configuration)
        self.client = PlaidApi(self.api_client)

    def create_link_token(self, user_id: str) -> CreateLinkTokenResponse:
        log.info(
            f"Creating link token for user '{user_id}' with webhook '{PlaidClient.WEBHOOK_URL}'"
        )
        request = LinkTokenCreateRequest(
            products=[
                Products("auth"),
                Products("transactions"),
                Products("investments"),
                Products("liabilities"),
            ],
            client_name=PlaidClient.CLIENT_NAME,
            country_codes=[CountryCode("US")],
            redirect_uri=PlaidClient.REDIRECT_URI,
            language="en",
            webhook=PlaidClient.WEBHOOK_URL,
            user=LinkTokenCreateRequestUser(client_user_id=user_id),
        )
        response = self.client.link_token_create(request).to_dict()
        return CreateLinkTokenResponse(
            link_token=response["link_token"],
            expiration=response["expiration"],
            request_id=response["request_id"],
            walter_user_id=user_id,
            plaid_user_id=response["user_id"],
        )

    def exchange_public_token(self, public_token: str) -> ExchangePublicTokenResponse:
        log.info("Exchanging Plaid public token for user access token")
        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = self.client.item_public_token_exchange(request)
        access_token = response["access_token"]
        item_id = response["item_id"]
        return ExchangePublicTokenResponse(
            public_token=public_token,
            access_token=access_token,
            item_id=item_id,
        )

    def sync_transactions(
        self, user_id: str, access_token: str, cursor: Optional[str]
    ) -> SyncTransactionsResponse:
        log.info(f"Syncing transactions for user '{user_id}'")

        added, modified, removed = [], [], []

        has_more = True
        while has_more:
            kwargs = {
                "access_token": access_token,
            }

            if cursor is not None:
                kwargs["cursor"] = cursor

            response = self.client.transactions_sync(TransactionsSyncRequest(**kwargs))

            added_transactions = [
                Transaction.from_plaid_transaction(user_id, transaction)
                for transaction in response["added"]
            ]
            modified_transactions = [
                Transaction.from_plaid_transaction(user_id, transaction)
                for transaction in response["modified"]
            ]
            removed_transactions = [
                Transaction.from_plaid_transaction(user_id, transaction)
                for transaction in response["removed"]
            ]

            added.extend(added_transactions)
            modified.extend(modified_transactions)
            removed.extend(removed_transactions)

            cursor = response["next_cursor"]
            has_more = response["has_more"]

        return SyncTransactionsResponse(
            cursor=cursor,
            synced_at=dt.datetime.now(dt.UTC),
            added_transactions=added,
            modified_transactions=modified,
            removed_transactions=removed,
        )

    def refresh_transactions(self, access_token: str) -> None:
        log.info("Refreshing user transactions for given access token...")
        response = self.client.transactions_refresh(
            TransactionsRefreshRequest(
                access_token=access_token,
            )
        )
        print(response.to_dict())
        log.info("Successfully refreshed user transactions!")

    def get_accounts(self, access_token: str) -> None:
        log.info("Getting accounts for user...")
        request = AccountsGetRequest(access_token=access_token)
        accounts_response = self.client.accounts_get(request)
        return accounts_response

    def _get_configuration(self) -> Configuration:
        return Configuration(
            host=self.environment,
            api_key={
                "clientId": self.client_id,
                "secret": self.secret,
            },
        )
