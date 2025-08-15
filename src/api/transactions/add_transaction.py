import datetime as dt
import json
from dataclasses import dataclass

from polygon.exceptions import BadResponse
from polygon.rest.models import TickerDetails

from src.ai.mlp.expenses import ExpenseCategorizerMLP
from src.api.common.exceptions import (
    BadRequest,
    NotAuthenticated,
    UserDoesNotExist,
    AccountDoesNotExist,
)
from src.database.securities.exchanges import get_market_exchange
from src.database.securities.models import Stock, Crypto
from src.api.common.exceptions import SecurityDoesNotExist
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import Response, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.accounts.models import Account
from src.database.accounts.models import AccountType
from src.database.client import WalterDB
from src.database.holdings.models import Holding
from src.database.securities.models import SecurityType
from src.database.transactions.models import (
    Transaction,
    TransactionType,
    TransactionCategory,
    InvestmentTransaction,
    BankTransaction,
    TransactionSubType,
    InvestmentTransactionSubType,
    BankingTransactionSubType,
)
from src.database.users.models import User
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
        BadRequest,
        NotAuthenticated,
        UserDoesNotExist,
        AccountDoesNotExist,
        SecurityDoesNotExist,
    ]

    walter_db: WalterDB
    transaction_categorizer: ExpenseCategorizerMLP
    polygon: PolygonClient

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
        expense_categorizer: ExpenseCategorizerMLP,
        polygon: PolygonClient,
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
        self.polygon = polygon

    def execute(self, event: dict, authenticated_email: str) -> Response:
        user = self._verify_user_exists(self.walter_db, authenticated_email)
        account = self._verify_account_exists(user, event)
        transaction = self._create_transaction(user, account, event)
        self.walter_db.add_transaction(transaction)
        return Response(
            api_name=AddTransaction.API_NAME,
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
        account = self.walter_db.get_account(user.user_id, account_id)

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
            date = dt.datetime.strptime(body["date"], "%Y-%m-%d")
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
        date: dt.datetime,
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

        log.info(f"Checking for security in database with ticker '{security_id}'")
        existing_security = self.walter_db.get_security_by_ticker(security_id)
        if not existing_security:
            log.info(f"Security with security_id '{security_id}' not found in database")

            # raise exception if security not found in polygon
            security_details = self._verify_security_exists(security_id, security_type)

            new_security = None
            match security_type:
                case SecurityType.STOCK:
                    price = self.polygon.get_latest_price(
                        security_details.ticker.upper(), SecurityType.STOCK
                    )
                    new_security = Stock.create(
                        name=security_details.name,
                        ticker=security_details.ticker.upper(),
                        exchange=get_market_exchange(
                            security_details.primary_exchange
                        ).key_name,
                        price=price,
                    )
                case SecurityType.CRYPTO:
                    price = self.polygon.get_latest_price(
                        security_details.ticker.upper(), SecurityType.CRYPTO
                    )
                    new_security = Crypto.create(
                        name=security_details.name,
                        ticker=security_details.ticker.upper(),
                        price=price,
                    )

            log.info(f"Adding security with security_id '{security_id}' to database")
            self.walter_db.put_security(new_security)

            # update existing security with new security details
            existing_security = new_security
        else:
            log.info(f"Security with security_id '{security_id}' found in database")
            log.info(existing_security.to_dict())

        match transaction_subtype:
            case InvestmentTransactionSubType.BUY:
                holding = self.walter_db.get_holding(
                    account.account_id, existing_security.security_id
                )

                if not holding:
                    log.info(
                        f"Holding not found for account '{account.account_id}' and security '{security_id}'"
                    )
                    holding = Holding.create_new_holding(
                        account_id=account.account_id,
                        security_id=existing_security.security_id,
                        quantity=quantity,
                        average_cost_basis=price_per_share,
                    )
                else:
                    holding.quantity += quantity
                    holding.total_cost_basis += quantity * price_per_share
                    holding.average_cost_basis = (
                        holding.total_cost_basis / holding.quantity
                    )

                self.walter_db.put_holding(holding)
            case InvestmentTransactionSubType.SELL:
                holding = self.walter_db.get_holding(
                    account.account_id, existing_security.security_id
                )

                if not holding:
                    raise BadRequest(f"No holding found for security_id {security_id}")
                elif holding.quantity < quantity:
                    raise BadRequest(
                        f"Not enough holding for security_id {security_id}"
                    )
                else:
                    holding.quantity -= quantity
                    holding.total_cost_basis = (
                        holding.quantity * holding.average_cost_basis
                    )

                self.walter_db.put_holding(holding)
            case _:
                raise BadRequest(
                    f"Invalid investment transaction subtype: {transaction_subtype}"
                )

        return InvestmentTransaction.create(
            account_id=account.account_id,
            user_id=user.user_id,
            date=date,
            transaction_type=transaction_type,
            transaction_subtype=transaction_subtype,
            transaction_category=transaction_category,
            ticker=security_id,
            exchange=(
                existing_security.exchange
                if isinstance(existing_security, Stock)
                else "CRYPTO"
            ),
            quantity=quantity,
            price_per_share=price_per_share,
        )

    def _create_bank_transaction(
        self,
        user: User,
        account: Account,
        date: dt.datetime,
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

    def _verify_security_exists(
        self, security_id: str, security_type: SecurityType
    ) -> TickerDetails:
        log.info(f"Verifying security exists for security_id '{security_id}'")
        try:
            return self.polygon.get_ticker_info(security_id, security_type)
        except BadResponse as e:
            if json.loads(str(e))["status"] == "NOT_FOUND":
                raise SecurityDoesNotExist(
                    f"Security with security_id '{security_id}' does not exist!"
                )
        except Exception as e:
            raise BadRequest(
                f"Error verifying security with security_id '{security_id}': {str(e)}"
            )
        log.info(
            f"Verified security exists for security_id '{security_id}' in Polygon!"
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True
