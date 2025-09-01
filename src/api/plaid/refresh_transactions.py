from dataclasses import dataclass
from typing import List, Optional

from src.api.common.exceptions import (
    BadRequest,
    NotAuthenticated,
    PlaidItemDoesNotExist,
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
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class RefreshTransactions(WalterAPIMethod):
    """
    WalterAPI: RefreshTransactions

    Refreshes transactions for all Plaid items linked to the user's account
    by triggering an on-demand sync with Plaid's refresh transactions API..

    This API allows manual refresh of transactions outside of:
    - Automated Plaid webhook updates
    - Scheduled periodic sync jobs
    """

    API_NAME = "RefreshTransactions"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer"}
    REQUIRED_FIELDS = []
    EXCEPTIONS = [
        (NotAuthenticated, HTTPStatus.UNAUTHORIZED),
        (PlaidItemDoesNotExist, HTTPStatus.NOT_FOUND),
        (UserDoesNotExist, HTTPStatus.NOT_FOUND),
        (BadRequest, HTTPStatus.BAD_REQUEST),
    ]

    plaid: PlaidClient

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        metrics: DatadogMetricsClient,
        db: WalterDB,
        plaid: PlaidClient,
    ) -> None:
        super().__init__(
            RefreshTransactions.API_NAME,
            RefreshTransactions.REQUIRED_QUERY_FIELDS,
            RefreshTransactions.REQUIRED_HEADERS,
            RefreshTransactions.REQUIRED_FIELDS,
            RefreshTransactions.EXCEPTIONS,
            walter_authenticator,
            metrics,
            db,
        )
        self.plaid = plaid

    def execute(self, event: dict, session: Optional[Session]) -> Response:
        # verify user and plaid item(s) exist
        user = self._verify_user_exists(session.user_id)
        items = self._get_plaid_items_for_user(user)

        # refresh transactions for each plaid item owned by the user
        for item in items:
            self._refresh_transactions(item)

        return Response(
            api_name=RefreshTransactions.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Transactions refreshed successfully!",
            data={
                "user": user.user_id,
                "num_items": len(items),
                "items": [item.get_item_id() for item in items],
            },
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True

    def _get_plaid_items_for_user(self, user: User) -> List[PlaidItem]:
        log.info(
            f"Getting Plaid items to refresh transactions for user: {user.user_id}"
        )
        items = self.db.get_plaid_items(user.user_id)
        if len(items) == 0:
            raise PlaidItemDoesNotExist(
                f"No Plaid items found for user '{user.user_id}'!"
            )
        log.info(
            f"Retrieved {len(items)} Plaid items to refresh transactions for user: {user.user_id}"
        )
        return items

    def _refresh_transactions(self, item: PlaidItem) -> None:
        log.info(f"Refreshing transactions for Plaid item: {item.item_id}")
        self.plaid.refresh_transactions(item.access_token)
        log.info(f"Refreshed transactions for Plaid item: {item.item_id}")
