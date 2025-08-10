import datetime as dt
import json
from dataclasses import dataclass

from src.ai.mlp.expenses import ExpenseCategorizerMLP
from src.api.common.exceptions import (
    BadRequest,
    NotAuthenticated,
    UserDoesNotExist,
    AccountDoesNotExist,
)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import Response, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.accounts.models import Account
from src.database.client import WalterDB
from src.database.transactions.models import Transaction
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
        AccountDoesNotExist,
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
        user = self._verify_user_exists(self.walter_db, authenticated_email)
        account = self._verify_account_exists(user.user_id, event)
        transaction = self._create_transaction(
            user_id=user.user_id, account_id=account.account_id, event=event
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

    def _verify_account_exists(self, user_id: str, event: dict) -> Account:
        """
        Verify that the account exists for the user.

        Args:
            user_id: The user ID of the account.
            event: The event containing the account data.

        Returns:
            (Account): The verified account object.
        """
        # get user account details from the event
        body = json.loads(event["body"])
        account_id = body["account_id"]
        log.info(
            f"Verifying account exists for user '{user_id}' with account_id '{account_id}'"
        )

        # check db to see if an account exists for the user
        account = self.walter_db.get_account(user_id=user_id, account_id=account_id)

        # if an account does not exist for the user, raise a user account does not exist exception
        if account is None:
            raise AccountDoesNotExist("Account does not exist for user!")

        log.info(f"Verified account '{account_id}' exists for user '{user_id}'!")

        return account

    def _create_transaction(
        self, user_id: str, account_id: str, event: dict
    ) -> Transaction:
        """
        Create a transaction object from the provided event.

        Args:
            user_id: The user ID of the transaction.
            account_id: The account ID of the transaction.
            event: The event containing the transaction data.

        Returns:
            (Transaction): The created transaction object.
        """
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

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True
