import datetime as dt
from dataclasses import dataclass
from typing import Optional

from plaid import ApiClient, Configuration
from plaid.api.plaid_api import PlaidApi
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
from src.database.client import WalterDB
from src.plaid.models import (
    CreateLinkTokenResponse,
    ExchangePublicTokenResponse,
    SyncTransactionsResponse,
)
from src.plaid.transaction_converter import TransactionConverter
from src.utils.log import Logger

LOG = Logger(__name__).get_logger()


@dataclass
class PlaidClient:
    """
    Plaid Client
    """

    CLIENT_NAME = CONFIG.plaid.client_name
    REDIRECT_URI = CONFIG.plaid.redirect_uri
    WEBHOOK_URL = CONFIG.plaid.sync_transactions_webhook_url

    walter_sm: WalterSecretsManagerClient
    walter_db: WalterDB
    environment: str
    transaction_converter: TransactionConverter

    # all the default none fields are lazily loaded
    # see _lazily_load_client method
    client_id: str = None
    secret: str = None
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
        LOG.info(
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
        LOG.info(f"Successfully created link token for user '{user_id}'")
        LOG.debug(f"Plaid LinkTokenCreate API response:\n{response}")
        return CreateLinkTokenResponse(
            request_id=response["request_id"],
            user_id=user_id,
            link_token=response["link_token"],
            expiration=response["expiration"],
        )

    def exchange_public_token(self, public_token: str) -> ExchangePublicTokenResponse:
        """
        Exchanges a Plaid public token for a user access token and item ID.

        This method calls Plaid's Item Public Token Exchange API to exchange the public
        token provided by the client for an access token and item ID, which are required
        for accessing user account information.

        Args:
            public_token (str): The public token obtained from Plaid Link.

        Returns:
            ExchangePublicTokenResponse: An object that contains the public token,
            access token, and item ID returned from the exchange process.
        """
        self._lazily_load_client()
        LOG.info("Exchanging Plaid public token for user access token")
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
        """
        Synchronizes transactions for a user by fetching added, modified, and removed
        transactions using the Plaid API, and converts them to a standard format.

        Args:
            user_id (str): The identifier of the user whose transactions will be
                synchronized.
            access_token (str): The access token for authenticating the API request.
            cursor (Optional[str]): The cursor for retrieving transactions incrementally.
                If None, the process starts from the beginning.

        Returns:
            SyncTransactionsResponse: Contains the cursor for the next sync, the time
                of synchronization, and lists of added, modified, and removed
                transactions.
        """
        self._lazily_load_client()
        LOG.info(f"Syncing transactions for user '{user_id}'")

        added, modified, removed = [], [], []
        has_more = True
        while has_more:
            LOG.info("Getting transactions...")

            kwargs = {
                "access_token": access_token,
            }

            if cursor is not None:
                kwargs["cursor"] = cursor

            response = self.client.transactions_sync(TransactionsSyncRequest(**kwargs))

            LOG.info("Getting newly added transactions...")
            added_transactions = []
            for plaid_transaction in response["added"]:
                transaction = self.transaction_converter.convert(plaid_transaction)
                added_transactions.append(transaction)

            LOG.info("Getting modified transactions...")
            modified_transactions = []
            for plaid_transaction in response["modified"]:
                transaction = self.transaction_converter.convert(plaid_transaction)
                modified_transactions.append(transaction)

            LOG.info("Getting removed transactions...")
            removed_transactions = []
            for plaid_transaction in response["removed"]:
                transaction = self.transaction_converter.convert(plaid_transaction)
                removed_transactions.append(transaction)

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
        LOG.info("Refreshing user transactions for given access token...")
        response = self.client.transactions_refresh(
            TransactionsRefreshRequest(
                access_token=access_token,
            )
        )
        LOG.debug(f"Plaid TransactionsRefresh API response:\n{response}")
        LOG.info("Successfully refreshed user transactions!")

    def _lazily_load_client(self) -> None:
        """
        Lazily loads the Plaid API client if it has not already been initialized.

        This function checks if the `client_id` and `secret` attributes of the
        instance are `None`. If either is `None`, it retrieves the Plaid
        credentials for the appropriate environment (e.g., sandbox or production)
        and initializes the client.

        Raises:
            RuntimeError: If the secrets manager fails to provide the required
                Plaid credentials.
        """
        if self.client_id is None or self.secret is None:
            self.client_id = self.walter_sm.get_plaid_client_id()
            self.secret = self.walter_sm.get_plaid_secret_key()
            self.client = PlaidApi(
                ApiClient(
                    Configuration(
                        host=self.environment,
                        api_key={
                            "clientId": self.client_id,
                            "secret": self.secret,
                        },
                    )
                )
            )
