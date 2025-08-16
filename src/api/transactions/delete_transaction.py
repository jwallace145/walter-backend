import datetime as dt
import json
from dataclasses import dataclass

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
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.transactions.models import (
    InvestmentTransaction,
    InvestmentTransactionSubType,
    Transaction,
    TransactionType,
)
from src.database.users.models import User
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class DeleteTransaction(WalterAPIMethod):
    """
    WalterAPI: DeleteTransaction

    This API deletes a user transaction from the Transactions table
    in WalterDB.
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
    ]

    walter_db: WalterDB

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            DeleteTransaction.API_NAME,
            DeleteTransaction.REQUIRED_QUERY_FIELDS,
            DeleteTransaction.REQUIRED_HEADERS,
            DeleteTransaction.REQUIRED_FIELDS,
            DeleteTransaction.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str) -> Response:
        user = self._verify_user_exists(self.walter_db, authenticated_email)
        transaction = self._verify_transaction_exists(user, event)
        self._delete_transaction(user, transaction)
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
        transaction = self.walter_db.get_user_transaction(
            user.user_id, transaction_id, transaction_date
        )
        if transaction is None:
            raise TransactionDoesNotExist(
                f"Transaction with ID '{transaction_id}' does not exist!"
            )

        log.info("Verified transaction exists!")

        return transaction

    def _delete_transaction(self, user: User, transaction: Transaction) -> None:
        log.info(
            f"Deleting transaction with ID '{transaction.transaction_id}' and date '{transaction.get_transaction_date()}'"
        )

        if transaction.transaction_type == TransactionType.INVESTMENT:
            log.info(
                "Updating investment holding as a result of deleting the investment transaction"
            )

            if isinstance(transaction, InvestmentTransaction):

                log.info(
                    f"Getting holding for account '{transaction.account_id}' and security '{transaction.security_id}'"
                )
                security = self.walter_db.get_security_by_ticker(
                    transaction.security_id
                )
                holding = self.walter_db.get_holding(
                    transaction.account_id, security.security_id
                )

                if not holding:
                    raise HoldingDoesNotExist(
                        f"Holding for account '{transaction.account_id}' and security '{transaction.security_id}' does not exist!"
                    )

                if transaction.transaction_subtype == InvestmentTransactionSubType.BUY:
                    log.info("Buy investment transaction! Updating holding...")
                    holding.quantity -= transaction.quantity
                    if holding.quantity <= 0:
                        self.walter_db.delete_holding(
                            transaction.account_id, holding.security_id
                        )
                    else:
                        holding.total_cost_basis -= (
                            transaction.quantity * transaction.price_per_share
                        )
                        holding.average_cost_basis = (
                            holding.total_cost_basis / holding.quantity
                        )
                        self.walter_db.put_holding(holding)
                elif (
                    transaction.transaction_subtype == InvestmentTransactionSubType.SELL
                ):
                    log.info("Sell investment transaction! Updating holding...")
                    holding.quantity += transaction.quantity
                    holding.total_cost_basis += (
                        transaction.quantity * transaction.price_per_share
                    )
                    holding.average_cost_basis = (
                        holding.total_cost_basis / holding.quantity
                    )
                    self.walter_db.put_holding(holding)
                else:
                    log.info(
                        "Transaction subtype is not a buy or sell! Skipping holding update"
                    )

            self.walter_db.delete_transaction(
                transaction.account_id,
                transaction.transaction_id,
                transaction.get_transaction_date(),
            )
