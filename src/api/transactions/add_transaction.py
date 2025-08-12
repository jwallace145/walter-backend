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
from src.database.transactions.models import (
    Transaction,
    TransactionType,
    TransactionCategory,
    InvestmentTransaction,
    BankTransaction,
)
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
        "amount",
        "transaction_type",
        "transaction_category",
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
        self.walter_db.create_transaction(transaction)
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
        Create a transaction object from the provided event using the new models.

        Args:
            user_id: The user ID of the transaction.
            account_id: The account ID of the transaction.
            event: The event containing the transaction data.

        Returns:
            (Transaction): The created transaction object.
        """
        body = (
            json.loads(event["body"])
            if isinstance(event.get("body"), str)
            else event.get("body", {})
        )

        # Base fields
        date = dt.datetime.strptime(body["date"], "%Y-%m-%d")
        amount = float(body["amount"])
        txn_type = TransactionType.from_string(body["transaction_type"])
        txn_category = TransactionCategory.from_string(body["transaction_category"])

        # Investment transactions (buy/sell)
        if txn_type in {TransactionType.BUY, TransactionType.SELL}:
            try:
                security_id = body["security_id"]
                quantity = float(body["quantity"])
                price_per_share = float(body["price_per_share"])
            except KeyError as e:
                raise BadRequest(
                    f"Missing required field for investment transaction: {str(e)}"
                )
            except ValueError:
                raise BadRequest(
                    "Invalid numeric value for quantity or price_per_share"
                )

            computed_amount = quantity * price_per_share
            # Validate amount consistency (allow small floating error)
            if abs(computed_amount - amount) > 0.01:
                raise BadRequest(
                    "Amount must equal quantity * price_per_share for investment transactions"
                )

            return InvestmentTransaction(
                account_id=account_id,
                user_id=user_id,
                transaction_type=txn_type,
                transaction_category=txn_category,
                transaction_date=date,
                transaction_amount=amount,
                security_id=security_id,
                quantity=quantity,
                price_per_share=price_per_share,
            )

        # Bank transactions (debit/credit/transfer)
        try:
            merchant_name = body["merchant_name"]
        except KeyError as e:
            raise BadRequest(f"Missing required field for bank transaction: {str(e)}")

        return BankTransaction(
            account_id=account_id,
            user_id=user_id,
            transaction_type=txn_type,
            transaction_category=txn_category,
            transaction_date=date,
            transaction_amount=amount,
            merchant_name=merchant_name,
        )

    def validate_fields(self, event: dict) -> None:
        # Validate base required fields and type-specific fields
        try:
            body = (
                json.loads(event["body"])
                if isinstance(event.get("body"), str)
                else event.get("body", {})
            )
        except Exception:
            raise BadRequest("Invalid JSON body")

        # Base fields (aligned with Transaction base model)
        base_required = [
            "account_id",
            "date",
            "amount",
            "transaction_type",
            "transaction_category",
        ]
        missing = [f for f in base_required if f not in body]
        if missing:
            raise BadRequest(f"Missing required fields: {missing}")

        # Validate date format
        try:
            dt.datetime.strptime(body["date"], "%Y-%m-%d")
        except Exception:
            raise BadRequest("Invalid date format. Expected YYYY-MM-DD")

        # Validate enums
        try:
            _ = TransactionType.from_string(body["transaction_type"])  # noqa: F841
            _ = TransactionCategory.from_string(
                body["transaction_category"]
            )  # noqa: F841
        except ValueError as e:
            raise BadRequest(str(e))

        # Validate amount is numeric
        try:
            float(body["amount"])  # ensure numeric
        except Exception:
            raise BadRequest("Invalid amount. Must be a number")

        # Type specific
        if body["transaction_type"].lower() in {"buy", "sell"}:
            inv_required = ["security_id", "quantity", "price_per_share"]
            missing_inv = [f for f in inv_required if f not in body]
            if missing_inv:
                raise BadRequest(
                    f"Missing required fields for investment transaction: {missing_inv}"
                )
            # numeric validation
            try:
                float(body["quantity"])  # noqa: F841
                float(body["price_per_share"])  # noqa: F841
            except Exception:
                raise BadRequest("Invalid quantity or price_per_share. Must be numbers")
        else:
            if "merchant_name" not in body:
                raise BadRequest(
                    "Missing required field for bank transaction: 'merchant_name'"
                )

    def is_authenticated_api(self) -> bool:
        return True
