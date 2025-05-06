import datetime as dt
import json
from dataclasses import dataclass

from src.ai.mlp.expenses import ExpenseCategorizerMLP
from src.api.common.exceptions import (
    BadRequest,
    NotAuthenticated,
    UserDoesNotExist,
    CashAccountDoesNotExist,
)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import Response, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.cash_accounts.models import CashAccount
from src.database.client import WalterDB
from src.database.transactions.models import Transaction
from src.database.users.models import User
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class AddTransaction(WalterAPIMethod):
    """
    WalterAPI: AddTransaction

    This API adds a user transaction to the Transactions table.
    """

    API_NAME = "AddTransaction"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer", "content-type": "application/json"}
    REQUIRED_FIELDS = [
        "account_id",
        "date",
        "vendor",
        "amount",
    ]
    EXCEPTIONS = [
        BadRequest,
        NotAuthenticated,
        UserDoesNotExist,
        CashAccountDoesNotExist,
    ]

    walter_db: WalterDB
    transaction_categorizer: ExpenseCategorizerMLP

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
        expense_categorizer: ExpenseCategorizerMLP,
    ) -> None:
        super().__init__(
            AddTransaction.API_NAME,
            AddTransaction.REQUIRED_QUERY_FIELDS,
            AddTransaction.REQUIRED_HEADERS,
            AddTransaction.REQUIRED_FIELDS,
            AddTransaction.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.transaction_categorizer = expense_categorizer

    def execute(self, event: dict, authenticated_email: str) -> Response:
        user = self._verify_user_exists(authenticated_email)
        account = self._verify_account_exists(user.user_id, event)
        transaction = self._get_transaction(
            user_id=user.user_id, account_id=account.get_account_id(), event=event
        )
        self.walter_db.put_transaction(transaction)
        return Response(
            api_name=AddTransaction.API_NAME,
            http_status=HTTPStatus.CREATED,
            status=Status.SUCCESS,
            message="Transaction added!",
            data={
                "transaction": transaction.to_dict(),
            },
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True

    def _verify_user_exists(self, email: str) -> User:
        log.info(f"Verifying user exists with email '{email}'")
        user = self.walter_db.get_user_by_email(email)
        if user is None:
            raise UserDoesNotExist(f"User with email '{email}' does not exist!")
        log.info("Verified user exists!")
        return user

    def _verify_account_exists(self, user_id: str, event: dict) -> CashAccount:
        body = json.loads(event["body"])
        account_id = body["account_id"]
        log.info(f"Verifying account exists for user with account_id '{account_id}'")

        # check db to see if account exists for user
        account = self.walter_db.get_cash_account(
            user_id=user_id, account_id=account_id
        )

        # if account does not exist for user, raise account does not exist exception
        if account is None:
            raise CashAccountDoesNotExist(
                f"Account with account_id '{account_id}' does not exist for user!"
            )

        log.info(f"Verified account '{account_id}' exists for user!")

        return account

    def _get_transaction(
        self, user_id: str, account_id: str, event: dict
    ) -> Transaction:
        body = json.loads(event["body"])
        date = dt.datetime.strptime(body["date"], "%Y-%m-%d")
        vendor = body["vendor"]
        amount = float(body["amount"])
        category = self.transaction_categorizer.categorize(vendor, amount)
        return Transaction(
            user_id=user_id,
            account_id=account_id,
            date=date,
            vendor=vendor,
            amount=amount,
            category=category,
            reviewed=False,
        )
