import json
from dataclasses import dataclass
from typing import List, Optional, Tuple

from src.api.common.exceptions import (
    BadRequest,
    NotAuthenticated,
    PlaidItemAlreadyExists,
    UserDoesNotExist,
)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Response, Status
from src.api.plaid.exchange_public_token.models import AccountDetails
from src.auth.authenticator import WalterAuthenticator
from src.database.accounts.models import Account
from src.database.client import WalterDB
from src.database.sessions.models import Session
from src.database.users.models import User
from src.environment import Domain
from src.metrics.client import DatadogMetricsClient
from src.plaid.client import PlaidClient
from src.plaid.models import ExchangePublicTokenResponse
from src.transactions.queue import (
    SyncUserTransactionsTask,
    SyncUserTransactionsTaskQueue,
)
from src.utils.log import Logger

LOG = Logger(__name__).get_logger()


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
    queue: SyncUserTransactionsTaskQueue

    def __init__(
        self,
        domain: Domain,
        walter_authenticator: WalterAuthenticator,
        metrics: DatadogMetricsClient,
        walter_db: WalterDB,
        plaid_client: PlaidClient,
        queue: SyncUserTransactionsTaskQueue,
    ) -> None:
        super().__init__(
            domain,
            ExchangePublicToken.API_NAME,
            ExchangePublicToken.REQUIRED_QUERY_FIELDS,
            ExchangePublicToken.REQUIRED_HEADERS,
            ExchangePublicToken.REQUIRED_FIELDS,
            ExchangePublicToken.EXCEPTIONS,
            walter_authenticator,
            metrics,
            walter_db,
        )
        self.plaid_client = plaid_client
        self.queue = queue

    def execute(self, event: dict, session: Optional[Session]) -> Response:
        """
        Executes the process of exchanging a public token for an access token and item ID,
        saves related account details to the database, and returns a success response.

        Args:
            event (dict): The input event containing details required for token exchange
                and account processing.
            session (Optional[Session]): The current session containing user-related
                authentication and context information.

        Returns:
            Response: A structured response indicating the result of the token exchange,
                including institution name and account-related data.
        """
        # verify user does exist in database before proceeding
        user: User = self._verify_user_exists(session.user_id)

        # get relevant details from event
        details: Tuple[str, List[AccountDetails]] = self._get_details_from_event(event)
        token, accounts = details

        # exchange the public token for an access token and item ID
        # the access token and item ID are stored in the database for future use
        response: ExchangePublicTokenResponse = self._exchange_token(token)

        # save the Plaid item and accounts to the database
        saved_accounts: List[Account] = self._save_accounts(response, user, accounts)

        # add sync transactions tasks for each saved account on initial
        # public token exchange with Plaid to populate transactions data
        self._add_sync_transactions_tasks(user.user_id, saved_accounts)

        # return successful exchange public token response
        return Response(
            domain=self.domain,
            api_name=ExchangePublicToken.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Tokens exchanged successfully!",
            data={
                "institution_name": "test",
                "num_accounts": len(accounts),
            },
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True

    def _get_details_from_event(self, event: dict) -> Tuple[str, List[AccountDetails]]:
        """
        Extracts and marshals details from an event, including public token, institution
        information, and account details, into structured formats for further processing.

        Args:
            event (dict): The input event containing the body with details such as
                `public_token`, `institution_id`, `institution_name`, and a set of
                account details.

        Returns:
            Tuple[str, List[AccountDetails]]: A tuple containing the public exchange token
                and a list of accounts associated with the public token and institution.
        """
        # load the event body into a dict for easy access
        body = json.loads(event["body"])

        public_token = body["public_token"]
        institution_id = body["institution_id"]
        institution_name = body["institution_name"]

        # marshal the included accounts into a list of dicts
        accounts: List[AccountDetails] = []
        for account in body["accounts"]:
            LOG.info(f"Account: {account}")
            accounts.append(
                AccountDetails(
                    institution_id=institution_id,
                    institution_name=institution_name,
                    account_id=account["account_id"],
                    account_name=account["account_name"],
                    account_type=account["account_type"],
                    account_subtype=account["account_subtype"],
                    account_last_four_numbers=account["account_last_four_numbers"],
                )
            )

        # return relevant details from event to caller
        return public_token, accounts

    def _exchange_token(self, public_token: str) -> ExchangePublicTokenResponse:
        """
        Exchanges a public token for an access token and item ID using the Plaid client.

        Args:
            public_token: The Plaid public token.

        Returns:
            The response from the Plaid client containing the access token and item ID.
        """
        LOG.info("Exchanging public token with the Plaid client")
        return self.plaid_client.exchange_public_token(public_token)

    def _save_accounts(
        self,
        response: ExchangePublicTokenResponse,
        user: User,
        accounts: List[AccountDetails],
    ) -> List[Account]:
        """
        Saves multiple Plaid accounts for a given user in the database.

        Processes the provided list of Plaid accounts, associates them with the
        specified user, and stores them in the database. Each account is linked
        to the user via their user ID, and includes relevant details such as
        account type, subtype, institution information, and Plaid-specific
        identifiers. The method ensures all accounts are saved and tracked
        appropriately.

        Args:
            response: Response containing Plaid access token and item ID
                needed for interaction with the Plaid API.
            user: User object representing the account owner for whom the
                Plaid accounts are being saved.
            accounts: List of account details consisting of account
                information retrieved from Plaid.

        Returns:
            List[Account]: A list of account objects corresponding to the
            saved accounts in the database.
        """
        LOG.info(f"Saving  {len(accounts)} Plaid accounts for user '{user.user_id}'")
        saved_accounts = []
        for account in accounts:
            LOG.debug(
                f"Saving account '{account.account_id}' for user '{user.user_id}'"
            )
            saved_accounts.append(
                self.db.create_account(
                    user_id=user.user_id,
                    account_type=account.account_type,
                    account_subtype=account.account_subtype,
                    institution_name=account.institution_name,
                    account_name=account.account_name,
                    account_mask=account.account_last_four_numbers,
                    balance=0.0,
                    plaid_institution_id=account.institution_id,
                    plaid_account_id=account.account_id,
                    plaid_access_token=response.access_token,
                    plaid_item_id=response.item_id,
                    plaid_last_sync_at=None,
                )
            )
            LOG.debug(f"Account '{account.account_id}' saved for user '{user.user_id}'")
        return saved_accounts

    def _add_sync_transactions_tasks(
        self, user_id: str, accounts: List[Account]
    ) -> None:
        """
        Adds synchronization tasks for account transactions to the task queue.

        This method iterates through a list of saved accounts and creates
        synchronization tasks for each account's transactions. These tasks are
        then added to the task queue to be processed asynchronously by the
        sync transactions workflow.

        Args:
            accounts (List[Account]): A list of saved accounts to initially
                sync transactions with Plaid.

        """
        plaid_item_ids = set([account.plaid_item_id for account in accounts])
        LOG.info(
            f"Adding sync transactions tasks for {len(plaid_item_ids)} Plaid items"
        )
        for plaid_item_id in plaid_item_ids:
            LOG.debug(
                f"Adding sync transactions task for Plaid item: '{plaid_item_id}'"
            )
            task = SyncUserTransactionsTask(user_id, plaid_item_id)
            task_id = self.queue.add_task(task)
            LOG.debug(f"Sync transactions task added to queue with ID '{task_id}'")
        LOG.info(f"Sync transactions tasks added for {len(accounts)} accounts")
