import datetime as dt
import json
from dataclasses import dataclass
from typing import Optional

from src.api.common.exceptions import (
    BadRequest,
    HoldingDoesNotExist,
    NotAuthenticated,
    TransactionDoesNotExist,
    UserDoesNotExist,
)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Response, Status
from src.auth.authenticator import WalterAuthenticator
from src.database.client import WalterDB
from src.database.sessions.models import Session
from src.database.transactions.models import (
    InvestmentTransaction,
    Transaction,
    TransactionType,
)
from src.database.users.models import User
from src.investments.holdings.exceptions import InvalidHoldingUpdate
from src.investments.holdings.updater import HoldingUpdater
from src.metrics.client import DatadogMetricsClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class DeleteTransaction(WalterAPIMethod):
    """
    WalterAPI: DeleteTransaction

    This API deletes a transaction from the database. For investment transactions,
    it also updates the associated holding.
    """

    API_NAME = "DeleteTransaction"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer", "content-type": "application/json"}
    REQUIRED_FIELDS = ["transaction_id", "date"]
    EXCEPTIONS = [
        BadRequest,
        NotAuthenticated,
        UserDoesNotExist,
        TransactionDoesNotExist,
        HoldingDoesNotExist,
        InvalidHoldingUpdate,
    ]

    holding_updater: HoldingUpdater

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        metrics: DatadogMetricsClient,
        walter_db: WalterDB,
        holding_updater: HoldingUpdater,
    ) -> None:
        super().__init__(
            DeleteTransaction.API_NAME,
            DeleteTransaction.REQUIRED_QUERY_FIELDS,
            DeleteTransaction.REQUIRED_HEADERS,
            DeleteTransaction.REQUIRED_FIELDS,
            DeleteTransaction.EXCEPTIONS,
            walter_authenticator,
            metrics,
            walter_db,
        )
        self.holding_updater = holding_updater

    def execute(self, event: dict, session: Optional[Session]) -> Response:
        user = self._verify_user_exists(session.user_id)
        transaction = self._verify_transaction_exists(user, event)
        self._delete_transaction(transaction)
        return Response(
            api_name=DeleteTransaction.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Transaction deleted!",
            data={"transaction": transaction.to_dict()},
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True

    def _verify_transaction_exists(self, user: User, event: dict) -> Transaction:
        log.info(f"Verifying transaction exists for user '{user.user_id}'")

        body = json.loads(event["body"])
        transaction_date = dt.datetime.strptime(body["date"], "%Y-%m-%d")
        transaction_id = body["transaction_id"]

        log.info(
            f"Getting transaction with ID '{transaction_id}' and date '{transaction_date}'"
        )
        transaction = self.db.get_user_transaction(
            user.user_id, transaction_id, transaction_date
        )
        if transaction is None:
            raise TransactionDoesNotExist(
                f"Transaction with ID '{transaction_id}' does not exist!"
            )

        log.info("Verified transaction exists!")

        return transaction

    def _delete_transaction(self, transaction: Transaction) -> None:
        log.info(
            f"Deleting transaction with ID '{transaction.transaction_id}' and date '{transaction.get_transaction_date()}'"
        )

        if transaction.transaction_type == TransactionType.INVESTMENT:
            log.info(
                "Updating investment holding as a result of deleting the investment transaction"
            )

            # update the associated holding due to transaction deletion
            if isinstance(transaction, InvestmentTransaction):
                self.holding_updater.delete_transaction(transaction)
            else:
                raise BadRequest(
                    f"Transaction {transaction} is not an instance of InvestmentTransaction!"
                )

        # after any side effects of deleting the transaction are handled, delete the transaction
        self.db.delete_transaction(
            transaction.account_id,
            transaction.transaction_id,
            transaction.get_transaction_date(),
        )
