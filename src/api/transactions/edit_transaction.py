import datetime as dt
import json
from dataclasses import dataclass

from src.api.common.exceptions import (
    BadRequest,
    NotAuthenticated,
    UserDoesNotExist,
    TransactionDoesNotExist,
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
    REQUIRED_FIELDS = [
        "transaction_date",  # sort key: <DATE>#<TRANSACTION_ID>
        "transaction_id",  # sort key: <DATE>#<TRANSACTION_ID>
        "updated_date",
        "updated_vendor",
        "updated_amount",
        "updated_category",
    ]
    EXCEPTIONS = [
        BadRequest,
        NotAuthenticated,
        UserDoesNotExist,
        TransactionDoesNotExist,
    ]

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
        transaction = self._verify_transaction_exists(user.user_id, event)
        updated_transaction = self._get_updated_transaction(transaction, event)
        self.walter_db.put_transaction(updated_transaction)
        return Response(
            api_name=EditTransaction.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Transaction edited!",
            data={
                "transaction": updated_transaction.to_dict(),
            },
        )

    def _verify_user_exists(self, email: str) -> User:
        log.info(f"Verifying user exists with email '{email}'")
        user = self.walter_db.get_user_by_email(email)
        if user is None:
            raise UserDoesNotExist(f"User with email '{email}' does not exist!")
        log.info("Verified user exists!")
        return user

    def _verify_transaction_exists(self, user_id: str, event: dict) -> Transaction:
        log.info("Verifying transaction exists")

        # get sort key fields of existing transaction from request body
        body = json.loads(event["body"])
        date = EditTransaction._get_date(body["transaction_date"])
        transaction_id = body["transaction_id"]

        # query walter db for existence of transaction
        transaction = self.walter_db.get_transaction(
            user_id=user_id,
            date=date,
            transaction_id=transaction_id,
        )

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

        # get static transaction id
        transaction_id = body["transaction_id"]

        # get updated transaction request body fields
        updated_date = EditTransaction._get_date(body["updated_date"])
        updated_vendor = body["updated_vendor"]
        updated_amount = EditTransaction._get_transaction_amount(body["updated_amount"])
        updated_category = EditTransaction._get_transaction_category(
            body["updated_category"]
        )

        # if user updated transaction date, delete and recreate transaction as
        # date is part of the primary key
        if updated_date != transaction.date:
            log.info(
                f"User updated transaction date! Deleting user transaction '{transaction_id}'"
            )
            self.walter_db.delete_transaction(
                user_id=transaction.user_id,
                date=transaction.date,
                transaction_id=transaction.transaction_id,
            )

        return Transaction(
            user_id=transaction.user_id,
            account_id=transaction.account_id,
            date=updated_date,
            vendor=updated_vendor,
            amount=updated_amount,
            category=updated_category,
            transaction_id=transaction_id,
            reviewed=True,
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
    def _get_transaction_amount(amount: str) -> float:
        try:
            return float(amount)
        except Exception:
            log.error(f"Invalid transaction amount: '{amount}'")
            raise BadRequest(f"Invalid transaction amount '{amount}'!")

    @staticmethod
    def _get_transaction_category(category: str) -> TransactionCategory:
        try:
            return TransactionCategory.from_string(category)
        except Exception:
            log.error(f"Invalid transaction category: '{category}'")
            raise BadRequest(f"Invalid transaction category '{category}'!")
