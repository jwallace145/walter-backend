import json
from dataclasses import dataclass
from typing import List, Optional

from src.api.common.exceptions import (
    BadRequest,
    NotAuthenticated,
    PlaidItemAlreadyExists,
    UserDoesNotExist,
)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Response, Status
from src.auth.authenticator import WalterAuthenticator
from src.database.client import WalterDB
from src.database.plaid_items.model import PlaidItem
from src.database.sessions.models import Session
from src.database.users.models import User
from src.metrics.client import DatadogMetricsClient
from src.plaid.client import PlaidClient
from src.plaid.models import ExchangePublicTokenResponse
from src.transactions.queue import (
    SyncUserTransactionsQueue,
    SyncUserTransactionsSQSEvent,
)
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class ExchangePublicToken(WalterAPIMethod):
    """
    WalterAPI: ExchangePublicToken

    Exchanges a temporary public token from Plaid Link for a permanent access token and item ID.
    This represents a single set of user credentials at a financial institution.

    The API:
    1. Exchanges the public token with Plaid to get an access token and item ID
    2. Stores these credentials in WalterDB for future authenticated Plaid API calls
    3. Uses the credentials to sync transactions, investments, and liabilities
    4. Creates corresponding accounts in WalterDB
    5. Triggers initial transaction sync via queue

    Key constraints:
    - Requires valid user authentication
    - Only one Plaid item allowed per user/institution combination
        - Prevents duplicate transaction syncs from webhook events for user/institution
          combinations

    Required fields:
    - public_token: Temporary public token from Plaid Link
    - institution_id: ID of the financial institution
    - institution_name: Display name of the institution
    - accounts: List of accounts to link from the institution
    """

    API_NAME = "ExchangePublicToken"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer", "content-type": "application/json"}
    REQUIRED_FIELDS = ["public_token", "institution_id", "institution_name", "accounts"]
    EXCEPTIONS = [
        (NotAuthenticated, HTTPStatus.UNAUTHORIZED),
        (BadRequest, HTTPStatus.BAD_REQUEST),
        (UserDoesNotExist, HTTPStatus.NOT_FOUND),
        (PlaidItemAlreadyExists, HTTPStatus.UNAUTHORIZED),
    ]

    walter_db: WalterDB
    plaid_client: PlaidClient
    queue: SyncUserTransactionsQueue

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        metrics: DatadogMetricsClient,
        walter_db: WalterDB,
        plaid_client: PlaidClient,
        queue: SyncUserTransactionsQueue,
    ) -> None:
        super().__init__(
            ExchangePublicToken.API_NAME,
            ExchangePublicToken.REQUIRED_QUERY_FIELDS,
            ExchangePublicToken.REQUIRED_HEADERS,
            ExchangePublicToken.REQUIRED_FIELDS,
            ExchangePublicToken.EXCEPTIONS,
            walter_authenticator,
            metrics,
        )
        self.walter_db = walter_db
        self.plaid_client = plaid_client
        self.queue = queue

    def execute(self, event: dict, session: Optional[Session]) -> Response:
        user = self._verify_user_exists(session.user_id)
        public_token = self._get_public_token(event)
        institution_id = self._get_institution_id(event)
        institution_name = self._get_institution_name(event)
        self._verify_user_institution_item_does_not_exist(user.user_id, institution_id)
        accounts = self._get_accounts(event)
        exchange_response = self._exchange_public_token(public_token)
        plaid_item = self._save_plaid_item(
            user.user_id,
            exchange_response.access_token,
            exchange_response.item_id,
            institution_id,
            institution_name,
        )
        self._save_accounts(user, institution_name, accounts)
        self._sync_user_transactions(user.user_id, plaid_item.get_item_id())
        return Response(
            api_name=ExchangePublicToken.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Tokens exchanged successfully!",
            data={
                "institution_name": institution_name,
                "num_accounts": len(accounts),
            },
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True

    def _get_public_token(self, event: dict) -> str:
        body = json.loads(event["body"])
        return body["public_token"]

    def _get_institution_id(self, event: dict) -> str:
        body = json.loads(event["body"])
        return body["institution_id"]

    def _get_institution_name(self, event: dict) -> str:
        body = json.loads(event["body"])
        return body["institution_name"]

    def _verify_user_institution_item_does_not_exist(
        self, user_id: str, institution_id: str
    ) -> None:
        item = self.walter_db.plaid_items_table.get_item_by_user_and_institution(
            user_id, institution_id
        )
        if item is not None:
            raise PlaidItemAlreadyExists(
                f"Plaid item already exists for user '{user_id}' and institution '{institution_id}'!"
            )
        else:
            log.info(
                f"Plaid item does not exist for user '{user_id}' and institution '{institution_id}'"
            )

    def _get_accounts(self, event: dict) -> List[dict]:
        body = json.loads(event["body"])

        accounts = []
        for account in body["accounts"]:
            accounts.append(
                {
                    "account_id": account["account_id"],
                    "account_name": account["account_name"],
                    "account_type": account["account_type"],
                    "account_subtype": account["account_subtype"],
                    "account_last_four_numbers": account[
                        "account_last_four_numbers"
                    ],  # account last four numbers
                }
            )

        return accounts

    def _exchange_public_token(self, public_token: str) -> ExchangePublicTokenResponse:
        """
        Exchanges a public token for an access token and item ID using the Plaid client.

        Args:
            public_token: The Plaid public token.

        Returns:
            The response from the Plaid client containing the access token and item ID.
        """
        log.info("Exchanging public token with the Plaid client")
        return self.plaid_client.exchange_public_token(public_token)

    def _save_plaid_item(
        self,
        user_id: str,
        access_token: str,
        item_id: str,
        institution_id: str,
        institution_name: str,
    ) -> PlaidItem:
        """
        Stores the resulting Plaid item in the database.

        Args:
            user: The authenticated user.
            exchange_response: The response containing the access token and item ID.
        """
        log.info(f"Saving Plaid item for '{institution_name}' for user '{user_id}'")
        plaid_item = self.walter_db.put_plaid_item(
            PlaidItem.create_item(
                user_id=user_id,
                item_id=item_id,
                access_token=access_token,
                institution_id=institution_id,
                institution_name=institution_name,
            )
        )
        log.info(f"Plaid item with item ID '{plaid_item.item_id}' saved successfully")
        return plaid_item

    def _save_accounts(
        self, user: User, institution_name: str, accounts: List[dict]
    ) -> None:
        log.info(f"Saving  {len(accounts)} Plaid accounts for user '{user.user_id}'")
        for account in accounts:
            # TODO: fix me!
            pass

    def _sync_user_transactions(self, user_id: str, plaid_item_id: str) -> None:
        log.info("Adding sync user transactions request to queue...")
        self.queue.add_sync_user_transactions_event(
            SyncUserTransactionsSQSEvent(user_id=user_id, plaid_item_id=plaid_item_id)
        )
