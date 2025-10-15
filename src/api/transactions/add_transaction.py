import datetime as dt
import json
from dataclasses import dataclass
from typing import Optional

from src.ai.mlp.expenses import ExpenseCategorizerMLP
from src.api.common.exceptions import (
    AccountDoesNotExist,
    BadRequest,
    NotAuthenticated,
    SecurityDoesNotExist,
    UserDoesNotExist,
)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Status
from src.api.common.response import Response
from src.auth.authenticator import WalterAuthenticator
from src.database.accounts.models import Account, AccountType
from src.database.client import WalterDB
from src.database.securities.models import SecurityType, Stock
from src.database.sessions.models import Session
from src.database.transactions.models import (
    BankingTransactionSubType,
    BankTransaction,
    InvestmentTransaction,
    InvestmentTransactionSubType,
    Transaction,
    TransactionCategory,
    TransactionSubType,
    TransactionType,
)
from src.database.users.models import User
from src.environment import Domain
from src.investments.holdings.exceptions import InvalidHoldingUpdate
from src.investments.holdings.updater import HoldingUpdater
from src.investments.securities.updater import SecurityUpdater
from src.metrics.client import DatadogMetricsClient
from src.polygon.client import PolygonClient
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
        "transaction_subtype",
        "transaction_category",
    ]
    EXCEPTIONS = [
        (BadRequest, HTTPStatus.BAD_REQUEST),
        (NotAuthenticated, HTTPStatus.UNAUTHORIZED),
        (UserDoesNotExist, HTTPStatus.NOT_FOUND),
        (AccountDoesNotExist, HTTPStatus.NOT_FOUND),
        (SecurityDoesNotExist, HTTPStatus.NOT_FOUND),
        (InvalidHoldingUpdate, HTTPStatus.BAD_REQUEST),
    ]

    transaction_categorizer: ExpenseCategorizerMLP
    polygon: PolygonClient
    holding_updater: HoldingUpdater
    security_updater: SecurityUpdater

    def __init__(
        self,
        domain: Domain,
        walter_authenticator: WalterAuthenticator,
        metrics: DatadogMetricsClient,
        walter_db: WalterDB,
        expense_categorizer: ExpenseCategorizerMLP,
        polygon: PolygonClient,
        holding_updater: HoldingUpdater,
        security_updater: SecurityUpdater,
    ) -> None:
        super().__init__(
            domain,
            AddTransaction.API_NAME,
            AddTransaction.REQUIRED_QUERY_FIELDS,
            AddTransaction.REQUIRED_HEADERS,
            AddTransaction.REQUIRED_FIELDS,
            AddTransaction.EXCEPTIONS,
            walter_authenticator,
            metrics,
            walter_db,
        )
        self.transaction_categorizer = expense_categorizer
        self.polygon = polygon
        self.holding_updater = holding_updater
        self.security_updater = security_updater

    def execute(self, event: dict, session: Optional[Session]) -> Response:
        user = self._verify_user_exists(session.user_id)
        account = self._verify_account_exists(user, event)
        transaction = self._create_transaction(user, account, event)

        # if the transaction is an investment transaction, update the holding
        if transaction.transaction_type == TransactionType.INVESTMENT and isinstance(
            transaction, InvestmentTransaction
        ):
            self.holding_updater.add_transaction(transaction)

        # add the transaction to the database
        self.db.add_transaction(transaction)

        return self._create_response(
            http_status=HTTPStatus.CREATED,
            status=Status.SUCCESS,
            message="Transaction added!",
            data={
                "transaction": transaction.to_dict(),
            },
        )

    def _verify_account_exists(self, user: User, event: dict) -> Account:
        """
        Verify that the account exists for the user.

        Args:
            user: The owner of the account.
            event: The event containing the account data.

        Returns:
            (Account): The verified account object.
        """
        # get user account details from the event
        body = json.loads(event["body"])
        account_id = body["account_id"]
        log.info(
            f"Verifying account exists for user '{user.user_id}' with account_id '{account_id}'"
        )

        # check db to see if an account exists for the user
        account = self.db.get_account(user.user_id, account_id)

        # if an account does not exist for the user, raise a user account does not exist exception
        if account is None:
            raise AccountDoesNotExist("Account does not exist for user!")

        log.info(f"Verified account '{account_id}' exists for user '{user.user_id}'!")

        return account

    def _create_transaction(
        self, user: User, account: Account, event: dict
    ) -> Transaction:
        """
        Create a transaction object from the provided event using the new models.

        Args:
            user: The owner of the transaction.
            account: The account of the transaction.
            event: The event containing the transaction data.

        Returns:
            (Transaction): The created transaction object.
        """
        body = json.loads(event["body"])

        try:
            date = dt.datetime.strptime(body["date"], "%Y-%m-%d").date()
        except Exception:
            raise BadRequest(f"Invalid date format: {body['date']}")

        try:
            amount = float(body["amount"])
        except Exception:
            raise BadRequest(f"Invalid transaction amount: '{body['amount']}'")

        txn_type = TransactionType.from_string(body["transaction_type"])
        txn_category = TransactionCategory.from_string(body["transaction_category"])

        match txn_type:
            case TransactionType.INVESTMENT:
                txn_subtype = InvestmentTransactionSubType.from_string(
                    body["transaction_subtype"]
                )
                return self._create_investment_transaction(
                    user,
                    account,
                    date,
                    amount,
                    txn_type,
                    txn_subtype,
                    txn_category,
                    body,
                )
            case TransactionType.BANKING:
                txn_subtype = BankingTransactionSubType.from_string(
                    body["transaction_subtype"]
                )
                return self._create_bank_transaction(
                    user,
                    account,
                    date,
                    amount,
                    txn_type,
                    txn_subtype,
                    txn_category,
                    body,
                )
            case _:
                raise BadRequest(f"Invalid transaction type: {txn_type}")

    def _create_investment_transaction(
        self,
        user: User,
        account: Account,
        date: dt.date,
        amount: float,
        transaction_type: TransactionType,
        transaction_subtype: TransactionSubType,
        transaction_category: TransactionCategory,
        body: dict,
    ) -> InvestmentTransaction:
        if account.account_type != AccountType.INVESTMENT:
            raise BadRequest(
                "Account type must be investment for investment transactions!"
            )

        # security_id, security_type, quantity, price_per_share are required for investment transactions
        try:
            security_id = body["security_id"]
            security_type = SecurityType.from_string(body["security_type"])
            quantity = float(body["quantity"])
            price_per_share = float(body["price_per_share"])
        except KeyError as e:
            raise BadRequest(
                f"Missing required field for investment transaction: {str(e)}"
            )
        except ValueError:
            raise BadRequest("Invalid numeric value for quantity or price_per_share")

        computed_amount = quantity * price_per_share

        # Validate amount consistency (allow small floating error)
        if abs(computed_amount - amount) > 0.01:
            raise BadRequest(
                "Amount must equal quantity * price_per_share for investment transactions"
            )

        # verify security exists in database or polygon before creating transaction
        security = self.security_updater.add_security_if_not_exists(
            security_id, security_type
        )

        # create transaction after verifying security exists in database or polygon
        return InvestmentTransaction.create(
            account_id=account.account_id,
            user_id=user.user_id,
            transaction_date=date,
            transaction_type=transaction_type,
            transaction_subtype=transaction_subtype,
            transaction_category=transaction_category,
            ticker=security_id,
            exchange=(security.exchange if isinstance(security, Stock) else "CRYPTO"),
            quantity=quantity,
            price_per_share=price_per_share,
        )

    def _create_bank_transaction(
        self,
        user: User,
        account: Account,
        date: dt.date,
        amount: float,
        transaction_type: TransactionType,
        transaction_subtype: TransactionSubType,
        transaction_category: TransactionCategory,
        body: dict,
    ) -> BankTransaction:
        if account.account_type not in [AccountType.CREDIT, AccountType.DEPOSITORY]:
            raise BadRequest(
                "Account type must be credit or depository for bank transactions!"
            )

        # merchant name is required for bank transactions
        try:
            merchant_name = body["merchant_name"]
        except KeyError as e:
            raise BadRequest(f"Missing required field for bank transaction: {str(e)}")

        return BankTransaction.create(
            account_id=account.account_id,
            user_id=user.user_id,
            transaction_type=transaction_type,
            transaction_subtype=transaction_subtype,
            transaction_category=transaction_category,
            transaction_date=date,
            transaction_amount=amount,
            merchant_name=merchant_name,
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True
