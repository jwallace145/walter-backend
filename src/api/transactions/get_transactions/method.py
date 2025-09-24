from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

from src.api.common.exceptions import (
    AccountDoesNotExist,
    BadRequest,
    NotAuthenticated,
    UserDoesNotExist,
)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Status
from src.api.common.response import Response
from src.auth.authenticator import WalterAuthenticator
from src.database.accounts.models import Account
from src.database.client import WalterDB
from src.database.sessions.models import Session
from src.database.transactions.models import (
    BankTransaction,
    InvestmentTransaction,
    Transaction,
    TransactionType,
)
from src.database.users.models import User
from src.environment import Domain
from src.metrics.client import DatadogMetricsClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class GetTransactions(WalterAPIMethod):
    """
    WalterAPI: GetTransactions

    This API gets the transactions for the user over a given
    period of time from the Transactions table in WalterDB.
    """

    API_NAME = "GetTransactions"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer"}
    REQUIRED_FIELDS = []
    EXCEPTIONS = [
        (BadRequest, HTTPStatus.BAD_REQUEST),
        (NotAuthenticated, HTTPStatus.UNAUTHORIZED),
        (AccountDoesNotExist, HTTPStatus.NOT_FOUND),
        (UserDoesNotExist, HTTPStatus.NOT_FOUND),
    ]

    def __init__(
        self,
        domain: Domain,
        walter_authenticator: WalterAuthenticator,
        metrics: DatadogMetricsClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            domain,
            GetTransactions.API_NAME,
            GetTransactions.REQUIRED_QUERY_FIELDS,
            GetTransactions.REQUIRED_HEADERS,
            GetTransactions.REQUIRED_FIELDS,
            GetTransactions.EXCEPTIONS,
            walter_authenticator,
            metrics,
            walter_db,
        )

    def execute(self, event: dict, session: Optional[Session]) -> Response:
        user: User = self._verify_user_exists(session.user_id)
        date_range: Tuple[datetime, datetime] = self._get_date_range(event)
        start_date, end_date = date_range
        account_id: Optional[str] = self._get_account_id(event)

        # if account_id is provided, get transactions for that account, else get transactions for user
        if account_id:
            account: Account = self._verify_account_exists(user, account_id)
            transactions: List[Transaction] = self.db.get_transactions_by_account(
                account.account_id, start_date, end_date
            )
            account_transactions: List[dict] = self._get_account_transactions(
                [account], transactions
            )
        else:
            accounts: List[Account] = self.db.get_accounts(user.user_id)
            transactions: List[Transaction] = self.db.get_transactions_by_user(
                user.user_id, start_date, end_date
            )
            account_transactions: List[dict] = self._get_account_transactions(
                accounts, transactions
            )

        total_income = sum(
            [
                transaction.transaction_amount
                for transaction in transactions
                if transaction.is_income()
            ]
        )
        total_expenses = sum(
            [
                transaction.transaction_amount
                for transaction in transactions
                if transaction.is_expense()
            ]
        )
        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Retrieved transactions!",
            data={
                "user_id": user.user_id,
                "num_transactions": len(transactions),
                "total_income": total_income,
                "total_expense": total_expenses,
                "cash_flow": total_income - total_expenses,
                "transactions": account_transactions,
            },
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True

    def _verify_account_exists(self, user: User, account_id: str) -> Account:
        """
        Verify that the account exists for the user.

        Args:
            user: The owner of the account.
            account_id: The ID of the account to verify.

        Returns:
            (Account): The verified account object.
        """
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

    def _get_date_range(self, event: dict) -> Tuple[datetime, datetime]:
        log.info("Getting optional date range from event...")

        # set default date range to min and max datetime values for a
        # complete history of transactions
        start_date = datetime.min
        end_date = datetime.max

        # reassign start and end dates if they are provided in the event
        start_date_str = WalterAPIMethod.get_query_field(event, "start_date")
        if start_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")

        end_date_str = WalterAPIMethod.get_query_field(event, "end_date")
        if end_date_str:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

        return start_date, end_date

    def _get_account_id(self, event: dict) -> Optional[str]:
        log.info("Getting optional account ID from event...")
        query_params = event.get("queryStringParameters") or {}
        account_id = query_params.get("account_id")
        if account_id:
            log.info(f"Found account ID: {account_id}")
        else:
            log.info("No account ID found in event!")
        return account_id

    def _get_account_transactions(
        self, accounts: List[Account], transactions: List[Transaction]
    ) -> List[dict]:
        accounts_dict = {}
        for account in accounts:
            accounts_dict[account.account_id] = account

        account_transactions = []
        for transaction in transactions:
            account = accounts_dict[transaction.account_id]
            match transaction.transaction_type:
                case TransactionType.INVESTMENT:
                    if isinstance(transaction, InvestmentTransaction):
                        account_transactions.append(
                            {
                                "account_id": account.account_id,
                                "transaction_id": transaction.transaction_id,
                                "security_id": transaction.security_id,
                                "account_institution_name": account.institution_name,
                                "account_name": account.account_name,
                                "account_type": account.account_type.value,
                                "account_mask": account.account_mask,
                                "transaction_date": transaction.transaction_date.split(
                                    "#"
                                )[0],
                                "transaction_type": transaction.transaction_type.value,
                                "transaction_subtype": transaction.transaction_subtype.value,
                                "transaction_category": transaction.transaction_category.value,
                                "price_per_share": transaction.price_per_share,
                                "quantity": transaction.quantity,
                                "transaction_amount": transaction.transaction_amount,
                                "is_plaid_transaction": transaction.is_plaid_transaction(),
                            }
                        )
                case TransactionType.BANKING:
                    if isinstance(transaction, BankTransaction):
                        account_transactions.append(
                            {
                                "account_id": account.account_id,
                                "transaction_id": transaction.transaction_id,
                                "account_institution_name": account.institution_name,
                                "account_name": account.account_name,
                                "account_type": account.account_type.value,
                                "account_mask": account.account_mask,
                                "transaction_type": transaction.transaction_type.value,
                                "transaction_subtype": transaction.transaction_subtype.value,
                                "transaction_category": transaction.transaction_category.value,
                                "transaction_date": transaction.transaction_date.split(
                                    "#"
                                )[0],
                                "merchant_name": transaction.merchant_name,
                                "transaction_amount": transaction.transaction_amount,
                                "is_plaid_transaction": transaction.is_plaid_transaction(),
                            }
                        )

        return account_transactions
