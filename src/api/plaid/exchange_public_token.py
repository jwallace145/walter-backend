import json
from dataclasses import dataclass
from typing import List

from src.api.common.exceptions import NotAuthenticated, UserDoesNotExist, BadRequest
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import Response, Status, HTTPStatus
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.cash_accounts.models import CashAccount, CashAccountType
from src.database.client import WalterDB
from src.database.plaid_items.model import PlaidItem
from src.database.users.models import User
from src.plaid.client import PlaidClient
from src.plaid.models import ExchangePublicTokenResponse
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class ExchangePublicToken(WalterAPIMethod):
    """
    WalterAPI: ExchangePublicToken
    """

    API_NAME = "ExchangePublicToken"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer", "content-type": "application/json"}
    REQUIRED_FIELDS = ["public_token", "institution_name", "accounts"]
    EXCEPTIONS = [NotAuthenticated, UserDoesNotExist, BadRequest]

    walter_db: WalterDB
    plaid_client: PlaidClient

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
        plaid_client: PlaidClient,
    ) -> None:
        super().__init__(
            ExchangePublicToken.API_NAME,
            ExchangePublicToken.REQUIRED_QUERY_FIELDS,
            ExchangePublicToken.REQUIRED_HEADERS,
            ExchangePublicToken.REQUIRED_FIELDS,
            ExchangePublicToken.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.plaid_client = plaid_client

    def execute(self, event: dict, authenticated_email: str) -> Response:
        user = self._verify_user_exists(authenticated_email)
        public_token = self._get_public_token(event)
        institution_name = self._get_institution_name(event)
        accounts = self._get_accounts(event)
        exchange_response = self._exchange_public_token(public_token)
        self._save_plaid_item(
            user.user_id,
            exchange_response.access_token,
            exchange_response.item_id,
            institution_name,
        )
        self._save_accounts(user, institution_name, accounts)
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

    def _verify_user_exists(self, email: str) -> User:
        """
        Verifies that a user exists based on their email.

        Args:
            email: The email of the user.

        Returns:
            The user object if found.

        Raises:
            UserDoesNotExist: If the user does not exist.
        """
        log.info(f"Verifying user existence for email '{email}'")
        user = self.walter_db.get_user_by_email(email)
        if user is None:
            raise UserDoesNotExist(f"User with email '{email}' does not exist!")
        log.info("User verified successfully!")
        return user

    def _get_public_token(self, event: dict) -> str:
        body = json.loads(event["body"])
        return body["public_token"]

    def _get_institution_name(self, event: dict) -> str:
        body = json.loads(event["body"])
        return body["institution_name"]

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
                    "account_mask": account[
                        "account_mask"
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
        institution_name: str,
    ) -> None:
        """
        Stores the resulting Plaid item in the database.

        Args:
            user: The authenticated user.
            exchange_response: The response containing the access token and item ID.
        """
        log.info(f"Saving Plaid item for '{institution_name}' for user '{user_id}'")
        plaid_item = self.walter_db.plaid_items_table.create_item(
            PlaidItem.create_item(
                user_id=user_id,
                item_id=item_id,
                access_token=access_token,
                institution_name=institution_name,
            )
        )
        log.info(f"Plaid item with item ID '{plaid_item.item_id}' saved successfully")

    def _save_accounts(
        self, user: User, institution_name: str, accounts: List[dict]
    ) -> None:
        log.info(f"Saving  {len(accounts)} Plaid accounts for user '{user.user_id}'")
        for account in accounts:
            self.walter_db.create_cash_account(
                CashAccount.create_account(
                    user=user,
                    bank_name=institution_name,
                    account_name=account["account_name"],
                    account_type=CashAccountType.CHECKING,
                    account_last_four_numbers=account["account_mask"],
                    balance=0.0,
                )
            )
