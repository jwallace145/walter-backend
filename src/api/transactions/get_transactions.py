import datetime as dt
from dataclasses import dataclass
from typing import List, Tuple

from src.api.common.exceptions import (AccountDoesNotExist, BadRequest,
                                       NotAuthenticated, UserDoesNotExist)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Response, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.accounts.models import Account
from src.database.client import WalterDB
from src.database.transactions.models import Transaction, TransactionType
from src.database.users.models import User
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
    REQUIRED_QUERY_FIELDS = ["start_date", "end_date"]
    REQUIRED_HEADERS = {"Authorization": "Bearer"}
    REQUIRED_FIELDS = []
    EXCEPTIONS = [
        BadRequest,
        NotAuthenticated,
        AccountDoesNotExist,
        UserDoesNotExist,
    ]

    walter_db: WalterDB

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            GetTransactions.API_NAME,
            GetTransactions.REQUIRED_QUERY_FIELDS,
            GetTransactions.REQUIRED_HEADERS,
            GetTransactions.REQUIRED_FIELDS,
            GetTransactions.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str) -> Response:
        # Ensure the authenticated user exists
        user = self._verify_user_exists(self.walter_db, authenticated_email)

        # Parse date range
        start_date, end_date = self._get_date_range(event)

        query_params = event.get("queryStringParameters") or {}
        account_id = query_params.get("account_id")

        # if account_id is provided, get transactions for that account, else get transactions for user
        if account_id:
            account = self._verify_account_exists(user, account_id)
            transactions = self.walter_db.get_transactions_by_account(
                account.account_id, start_date, end_date
            )
            account_transactions = self._get_account_transactions(
                [account], transactions
            )
        else:
            accounts = self.walter_db.get_accounts(user.user_id)
            transactions = self.walter_db.get_transactions_by_user(
                user.user_id, start_date, end_date
            )
            account_transactions = self._get_account_transactions(
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
        return Response(
            api_name=GetTransactions.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Retrieved transactions!",
            data={
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
        account = self.walter_db.get_account(user.user_id, account_id)

        # if an account does not exist for the user, raise a user account does not exist exception
        if account is None:
            raise AccountDoesNotExist("Account does not exist for user!")

        log.info(f"Verified account '{account_id}' exists for user '{user.user_id}'!")

        return account

    def _get_date_range(self, event: dict) -> Tuple[dt.datetime, dt.datetime]:
        start_date = dt.datetime.strptime(
            WalterAPIMethod.get_query_field(event, "start_date"), "%Y-%m-%d"
        )
        end_date = dt.datetime.strptime(
            WalterAPIMethod.get_query_field(event, "end_date"), "%Y-%m-%d"
        )
        return start_date, end_date

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
                    account_transactions.append(
                        {
                            "user_id": account.user_id,
                            "account_id": account.account_id,
                            "transaction_id": transaction.transaction_id,
                            "security_id": transaction.security_id,
                            "account_institution_name": account.institution_name,
                            "account_name": account.account_name,
                            "account_type": account.account_type.value,
                            "account_mask": account.account_mask,
                            "transaction_date": transaction.transaction_date.split("#")[
                                0
                            ],
                            "transaction_type": transaction.transaction_type.value,
                            "transaction_subtype": transaction.transaction_subtype.value,
                            "transaction_category": transaction.transaction_category.value,
                            "price_per_share": transaction.price_per_share,
                            "quantity": transaction.quantity,
                            "transaction_amount": transaction.transaction_amount,
                        }
                    )
                case TransactionType.BANKING:
                    account_transactions.append(
                        {
                            "user_id": account.user_id,
                            "account_id": account.account_id,
                            "transaction_id": transaction.transaction_id,
                            "account_institution_name": account.institution_name,
                            "account_name": account.account_name,
                            "account_type": account.account_type.value,
                            "account_mask": account.account_mask,
                            "transaction_type": transaction.transaction_type.value,
                            "transaction_subtype": transaction.transaction_subtype.value,
                            "transaction_category": transaction.transaction_category.value,
                            "transaction_date": transaction.transaction_date.split("#")[
                                0
                            ],
                            "merchant_name": transaction.merchant_name,
                            "transaction_amount": transaction.transaction_amount,
                        }
                    )

        return account_transactions
