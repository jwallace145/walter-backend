import datetime as dt
from dataclasses import dataclass
from typing import Optional

from plaid import ApiClient, Configuration
from plaid.api.plaid_api import PlaidApi
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.transactions_refresh_request import TransactionsRefreshRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.config import CONFIG
from src.database.transactions.models import Transaction
from src.plaid.models import (
    CreateLinkTokenResponse,
    ExchangePublicTokenResponse,
    SyncTransactionsResponse,
)
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class PlaidClient:
    """
    Plaid Client
    """

    CLIENT_NAME = CONFIG.plaid.client_name
    REDIRECT_URI = CONFIG.plaid.redirect_uri
    WEBHOOK_URL = CONFIG.plaid.sync_transactions_webhook_url

    walter_sm: WalterSecretsManagerClient
    environment: str

    # all the default none fields set during post-int
    client_id: str = None
    secret: str = None
    configuration: Configuration = None
    api_client: ApiClient = None
    client: PlaidApi = None

    def create_link_token(self, user_id: str) -> CreateLinkTokenResponse:
        """
        Creates a link token for the specified user to initiate the Plaid integration.

        This method generates a new link token for a given user ID using the Plaid
        API. The link token is required for embedding Plaid Link within your
        application and allows you to specify various configurations like products,
        webhook URL, and other details.

        Args:
            user_id (str): The unique identifier for the user for whom the link
                token is being created.

        Returns:
            CreateLinkTokenResponse: An object containing the details of the created
                link token, including the request ID, user ID, token value, and
                expiration date.

        Raises:
            Any exceptions returned by the Plaid API client during token creation
            (e.g., network errors, invalid configurations, or API failures).
        """
        self._lazily_load_client()
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
        log.info(f"Successfully created link token for user '{user_id}'")
        log.debug(f"Plaid LinkTokenCreate API response:\n{response}")
        return CreateLinkTokenResponse(
            request_id=response["request_id"],
            user_id=user_id,
            link_token=response["link_token"],
            expiration=response["expiration"],
        )

    def exchange_public_token(self, public_token: str) -> ExchangePublicTokenResponse:
        self._lazily_load_client()
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
        self._lazily_load_client()
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
        self._lazily_load_client()
        log.info("Refreshing user transactions for given access token...")
        response = self.client.transactions_refresh(
            TransactionsRefreshRequest(
                access_token=access_token,
            )
        )
        log.debug(f"Plaid TransactionsRefresh API response:\n{response}")
        log.info("Successfully refreshed user transactions!")

    def get_accounts(self, access_token: str) -> None:
        self._lazily_load_client()
        log.info("Getting accounts for user...")
        request = AccountsGetRequest(access_token=access_token)
        accounts_response = self.client.accounts_get(request)
        return accounts_response

    def _lazily_load_client(self) -> None:
        if self.client_id is None or self.secret is None:
            # TODO: Update secrets manager to get the plaid credentials by environment, e.g.: dev -> sandbox, prod -> prod
            self.client_id = self.walter_sm.get_plaid_sandbox_credentials_client_id()
            self.secret = self.walter_sm.get_plaid_sandbox_credentials_secret_key()
            self.configuration = self._get_configuration()
            self.api_client = ApiClient(self.configuration)
            self.client = PlaidApi(self.api_client)

    def _get_configuration(self) -> Configuration:
        return Configuration(
            host=self.environment,
            api_key={
                "clientId": self.client_id,
                "secret": self.secret,
            },
        )
