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
from src.auth.authenticator import WalterAuthenticator
from src.database.client import WalterDB
from src.database.sessions.models import Session
from src.database.users.models import User
from src.environment import Domain
from src.metrics.client import DatadogMetricsClient
from src.plaid.client import PlaidClient
from src.plaid.models import ExchangePublicTokenResponse
from src.transactions.queue import (
    SyncUserTransactionsQueue,
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
        domain: Domain,
        walter_authenticator: WalterAuthenticator,
        metrics: DatadogMetricsClient,
        walter_db: WalterDB,
        plaid_client: PlaidClient,
        queue: SyncUserTransactionsQueue,
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
        user = self._verify_user_exists(session.user_id)

        # get relevant details from event
        public_token, institution_id, institution_name, accounts = (
            self._get_details_from_event(event)
        )

        # exchange the public token for an access token and item ID
        # the access token and item ID are stored in the database for future use
        self._exchange_token(public_token)

        # save the Plaid item and accounts to the database
        self._save_accounts(user, institution_name, accounts)

        # return a successful response
        return Response(
            domain=self.domain,
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

    def _get_details_from_event(self, event: dict) -> Tuple[str, str, str, List[dict]]:
        """
        Extracts and marshals details from an event, including public token, institution
        information, and account details, into structured formats for further processing.

        Args:
            event (dict): The input event containing the body with details such as
                `public_token`, `institution_id`, `institution_name`, and a set of
                account details.

        Returns:
            Tuple[str, str, str, List[dict]]: A tuple containing the public token,
            institution ID, institution name, and a list of dictionaries
            representing accounts with their respective details.
        """
        # load the event body into a dict for easy access
        body = json.loads(event["body"])

        # marshal the included accounts into a list of dicts
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

        # return relevant details from event to caller
        return (
            body["public_token"],
            body["institution_id"],
            body["institution_name"],
            accounts,
        )

    def _exchange_token(self, public_token: str) -> ExchangePublicTokenResponse:
        """
        Exchanges a public token for an access token and item ID using the Plaid client.

        Args:
            public_token: The Plaid public token.

        Returns:
            The response from the Plaid client containing the access token and item ID.
        """
        log.info("Exchanging public token with the Plaid client")
        return self.plaid_client.exchange_public_token(public_token)

    def _save_accounts(
        self, user: User, institution_name: str, accounts: List[dict]
    ) -> None:
        log.info(f"Saving  {len(accounts)} Plaid accounts for user '{user.user_id}'")
        for account in accounts:
            # TODO: fix me!
            pass
