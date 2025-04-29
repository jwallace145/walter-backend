import datetime as dt
import json
from dataclasses import dataclass

from src.api.common.exceptions import (
    BadRequest,
    NotAuthenticated,
    UserDoesNotExist,
)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import Response, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.transactions.models import Transaction, TransactionCategory
from src.database.users.models import User
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
    REQUIRED_FIELDS = ["date", "transaction_id", "vendor", "amount", "category"]
    EXCEPTIONS = [BadRequest, NotAuthenticated, UserDoesNotExist]

    walter_db: WalterDB

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            EditTransaction.API_NAME,
            EditTransaction.REQUIRED_QUERY_FIELDS,
            EditTransaction.REQUIRED_HEADERS,
            EditTransaction.REQUIRED_FIELDS,
            EditTransaction.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str) -> Response:
        user = self._verify_user_exists(authenticated_email)
        transaction = self._get_transaction(user.user_id, event)
        self.walter_db.put_transaction(transaction)
        return Response(
            api_name=EditTransaction.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Transaction edited!",
            data={
                "transaction": transaction.to_dict(),
            },
        )

    def _verify_user_exists(self, email: str) -> User:
        log.info(f"Verifying user exists with email '{email}'")
        user = self.walter_db.get_user_by_email(email)
        if user is None:
            raise UserDoesNotExist(f"User with email '{email}' does not exist!")
        log.info("Verified user exists!")
        return user

    def _get_transaction(self, user_id: str, event: dict) -> Transaction:
        body = json.loads(event["body"])
        date = EditTransaction._get_date(body["date"])
        transaction_id = body["transaction_id"]
        vendor = body["vendor"]
        amount = EditTransaction._get_expense_amount(body["amount"])
        category = EditTransaction._get_expense_category(body["category"])
        return Transaction(
            user_id=user_id,
            date=date,
            vendor=vendor,
            amount=amount,
            category=category,
            transaction_id=transaction_id,
        )

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
    def _get_expense_amount(amount: str) -> float:
        try:
            return float(amount)
        except Exception:
            log.error(f"Invalid expense amount: {amount}")
            raise BadRequest(f"Invalid expense amount '{amount}'!")

    @staticmethod
    def _get_expense_category(category: str) -> TransactionCategory:
        try:
            return TransactionCategory.from_string(category)
        except Exception:
            log.error(f"Invalid expense category: {category}")
            raise BadRequest(f"Invalid expense category '{category}'!")
