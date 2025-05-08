import json
from dataclasses import dataclass

from src.api.common.exceptions import NotAuthenticated, UserDoesNotExist, BadRequest
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import Response, Status, HTTPStatus
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
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
    REQUIRED_FIELDS = ["public_token", "institution_name"]
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
        exchange_response = self._exchange_public_token(public_token)
        self._save_plaid_item(
            user.user_id,
            exchange_response.access_token,
            exchange_response.item_id,
            institution_name,
        )
        return Response(
            api_name=ExchangePublicToken.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Public token exchanged successfully!",
            data={
                "item_id": exchange_response.item_id,
                "access_token": exchange_response.access_token,
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
        log.info("Storing Plaid item in the database")
        plaid_item = self.walter_db.plaid_items_table.create_item(
            PlaidItem.create_item(
                user_id=user_id,
                item_id=item_id,
                access_token=access_token,
                institution_name=institution_name,
            )
        )
        log.info(f"Plaid item with item ID '{plaid_item.item_id}' stored successfully.")
