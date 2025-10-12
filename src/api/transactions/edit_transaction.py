import datetime as dt
import json
from dataclasses import dataclass
from typing import Optional

from src.api.common.exceptions import (
    BadRequest,
    NotAuthenticated,
    TransactionDoesNotExist,
    UserDoesNotExist,
)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Status
from src.api.common.response import Response
from src.auth.authenticator import WalterAuthenticator
from src.database.client import WalterDB
from src.database.securities.models import SecurityType
from src.database.sessions.models import Session
from src.database.transactions.models import (
    InvestmentTransaction,
    Transaction,
    TransactionCategory,
    TransactionType,
)
from src.database.users.models import User
from src.environment import Domain
from src.investments.holdings.updater import HoldingUpdater
from src.investments.securities.updater import SecurityUpdater
from src.metrics.client import DatadogMetricsClient
from src.polygon.client import PolygonClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class EditTransaction(WalterAPIMethod):
    """
    WalterAPI: EditTransaction

    This API edits an existing user transaction and updates the
    Transactions table in WalterDB accordingly.
    """

    API_NAME = "EditTransaction"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer", "content-type": "application/json"}
    REQUIRED_FIELDS = [
        "transaction_date",
        "transaction_id",
        "updated_merchant_name",
        "updated_category",
    ]
    EXCEPTIONS = [
        (BadRequest, HTTPStatus.BAD_REQUEST),
        (NotAuthenticated, HTTPStatus.UNAUTHORIZED),
        (UserDoesNotExist, HTTPStatus.NOT_FOUND),
        (TransactionDoesNotExist, HTTPStatus.NOT_FOUND),
    ]

    polygon: PolygonClient
    holding_updater: HoldingUpdater
    security_updater: SecurityUpdater

    def __init__(
        self,
        domain: Domain,
        walter_authenticator: WalterAuthenticator,
        metrics: DatadogMetricsClient,
        walter_db: WalterDB,
        polygon: PolygonClient,
        holding_updater: HoldingUpdater,
        security_updater: SecurityUpdater,
    ) -> None:
        super().__init__(
            domain,
            EditTransaction.API_NAME,
            EditTransaction.REQUIRED_QUERY_FIELDS,
            EditTransaction.REQUIRED_HEADERS,
            EditTransaction.REQUIRED_FIELDS,
            EditTransaction.EXCEPTIONS,
            walter_authenticator,
            metrics,
            walter_db,
        )
        self.polygon = polygon
        self.holding_updater = holding_updater
        self.security_updater = security_updater

    def execute(self, event: dict, session: Optional[Session]) -> Response:
        user = self._verify_user_exists(session.user_id)
        transaction = self._verify_transaction_exists(user, event)
        updated_transaction = self._get_updated_transaction(transaction, event)

        # if investment transaction, update holdings
        if isinstance(updated_transaction, InvestmentTransaction):
            self.holding_updater.update_transaction(updated_transaction)

        self.db.update_transaction(updated_transaction)

        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Transaction edited!",
            data={
                "transaction": updated_transaction.to_dict(),
            },
        )

    def _verify_transaction_exists(self, user: User, event: dict) -> Transaction:
        log.info("Verifying transaction exists")

        # get sort key fields of existing transaction from request body
        body = json.loads(event["body"])
        date = EditTransaction._get_date(body["transaction_date"])
        transaction_id = body["transaction_id"]

        # query walter db for existence of transaction
        transaction = self.db.get_user_transaction(user.user_id, transaction_id, date)

        # raise transaction does not exist exception if transaction not found in db
        if transaction is None:
            raise TransactionDoesNotExist(
                f"Transaction '{transaction_id}' on date '{date}' does not exist!"
            )

        log.info(f"Verified transaction '{transaction_id}' exists!")
        return transaction

    def _get_updated_transaction(
        self, transaction: Transaction, event: dict
    ) -> Transaction:
        body = json.loads(event["body"])

        # get updated transaction category from request body
        try:
            updated_transaction_category = TransactionCategory.from_string(
                body["updated_category"]
            )
        except ValueError:
            raise BadRequest(
                f"Invalid transaction category: '{body['updated_category']}'"
            )

        # update transaction based on transaction type
        match transaction.transaction_type:
            case TransactionType.INVESTMENT:
                # TODO: Implement updating investment transactions
                raise NotImplementedError(
                    "Updating investment transactions not supported!"
                )
            case TransactionType.BANKING:
                # get required fields for banking transaction from request body
                try:
                    updated_merchant_name = body["updated_merchant_name"]
                except KeyError as e:
                    raise BadRequest(
                        f"Missing required field for bank transaction: {str(e)}"
                    )
                # update the modified fields for the transaction
                transaction.merchant_name = updated_merchant_name
                transaction.transaction_category = updated_transaction_category
                return transaction

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True

    @staticmethod
    def _get_date(date: str) -> dt.datetime:
        try:
            return dt.datetime.strptime(date, "%Y-%m-%d")
        except Exception:
            log.error(f"Invalid date: {date}")
            raise BadRequest(f"Invalid date '{date}'!")

    @staticmethod
    def _get_transaction_amount(amount: str) -> float:
        try:
            return float(amount)
        except Exception:
            log.error(f"Invalid transaction amount: '{amount}'")
            raise BadRequest(f"Invalid transaction amount '{amount}'!")

    @staticmethod
    def _get_security_type(security_id: str) -> SecurityType:
        if security_id.split("-")[1] == "crypto":
            return SecurityType.CRYPTO
        return SecurityType.STOCK
