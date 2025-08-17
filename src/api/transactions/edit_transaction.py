import datetime as dt
import json
from dataclasses import dataclass

from src.api.common.exceptions import (
    BadRequest,
    NotAuthenticated,
    TransactionDoesNotExist,
    UserDoesNotExist,
)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Response, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.securities.models import SecurityType
from src.database.transactions.models import (
    BankingTransactionSubType,
    BankTransaction,
    InvestmentTransaction,
    InvestmentTransactionSubType,
    Transaction,
    TransactionCategory,
    TransactionType,
)
from src.database.users.models import User
from src.investments.holdings.updater import HoldingUpdater
from src.investments.securities.updater import SecurityUpdater
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
        "updated_date",
        "updated_amount",
        "updated_category",
        "updated_transaction_type",
        "updated_transaction_subtype",
        "updated_transaction_category",
    ]
    EXCEPTIONS = [
        BadRequest,
        NotAuthenticated,
        UserDoesNotExist,
        TransactionDoesNotExist,
    ]

    walter_db: WalterDB
    polygon: PolygonClient
    holding_updater: HoldingUpdater
    security_updater: SecurityUpdater

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
        polygon: PolygonClient,
        holding_updater: HoldingUpdater,
        security_updater: SecurityUpdater,
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
        self.polygon = polygon
        self.holding_updater = holding_updater
        self.security_updater = security_updater

    def execute(self, event: dict, authenticated_email: str) -> Response:
        user = self._verify_user_exists(self.walter_db, authenticated_email)
        transaction = self._verify_transaction_exists(user, event)
        updated_transaction = self._get_updated_transaction(transaction, event)

        # if investment transaction, update holdings
        if isinstance(updated_transaction, InvestmentTransaction):
            self.holding_updater.update_transaction(updated_transaction)

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

    def _verify_transaction_exists(self, user: User, event: dict) -> Transaction:
        log.info("Verifying transaction exists")

        # get sort key fields of existing transaction from request body
        body = json.loads(event["body"])
        date = EditTransaction._get_date(body["transaction_date"])
        transaction_id = body["transaction_id"]

        # query walter db for existence of transaction
        transaction = self.walter_db.get_user_transaction(
            user.user_id, transaction_id, date
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
        updated_amount = EditTransaction._get_transaction_amount(body["updated_amount"])
        updated_transaction_type = TransactionType.from_string(
            body["updated_transaction_type"]
        )
        updated_transaction_category = TransactionCategory.from_string(
            body["updated_transaction_category"]
        )

        # if user updated transaction date, delete and recreate transaction as
        # date is part of the primary key
        if updated_date != transaction.get_transaction_date():
            log.info(
                f"User updated transaction date! Deleting user transaction '{transaction_id}'"
            )

            # update holding if investment transaction
            if isinstance(transaction, InvestmentTransaction):
                self.holding_updater.delete_transaction(transaction)

            # delete the transaction
            self.walter_db.delete_transaction(
                account_id=transaction.account_id,
                transaction_id=transaction.transaction_id,
                date=transaction.get_transaction_date(),
            )

        match transaction.transaction_type:
            case TransactionType.INVESTMENT:
                # get required fields for investment transaction from request body
                try:
                    transaction_subtype = InvestmentTransactionSubType.from_string(
                        body["updated_transaction_subtype"]
                    )
                    ticker = body["ticker"]
                    exchange = body["exchange"]
                except KeyError as e:
                    raise BadRequest(
                        f"Missing required field for investment transaction: {str(e)}"
                    )

                security_type = EditTransaction._get_security_type(ticker)
                self.security_updater.add_security_if_not_exists(ticker, security_type)

                return InvestmentTransaction.create(
                    user_id=transaction.user_id,
                    account_id=transaction.account_id,
                    date=updated_date,
                    ticker=ticker,
                    exchange=exchange,
                    transaction_type=updated_transaction_type,
                    transaction_subtype=transaction_subtype,
                    transaction_category=updated_transaction_category,
                )
            case TransactionType.BANKING:
                # get required fields for banking transaction from request body
                try:
                    transaction_subtype = BankingTransactionSubType.from_string(
                        body["updated_transaction_subtype"]
                    )
                    merchant_name = body["merchant_name"]
                except KeyError as e:
                    raise BadRequest(
                        f"Missing required field for bank transaction: {str(e)}"
                    )

                return BankTransaction.create(
                    user_id=transaction.user_id,
                    account_id=transaction.account_id,
                    transaction_type=updated_transaction_type,
                    transaction_subtype=transaction_subtype,
                    transaction_category=updated_transaction_category,
                    transaction_date=updated_date,
                    transaction_amount=updated_amount,
                    merchant_name=merchant_name,
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
    def _get_security_type(security_id: str) -> SecurityType:
        if security_id.split("-")[1] == "crypto":
            return SecurityType.CRYPTO
        return SecurityType.STOCK
