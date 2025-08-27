import datetime as dt
from dataclasses import dataclass
from typing import List, Optional

from src.auth.authenticator import WalterAuthenticator
from src.aws.dynamodb.client import WalterDDBClient
from src.database.accounts.models import Account
from src.database.accounts.table import AccountsTable
from src.database.holdings.models import Holding
from src.database.holdings.table import HoldingsTable
from src.database.securities.models import Security
from src.database.securities.table import SecuritiesTable
from src.database.sessions.models import Session
from src.database.sessions.table import SessionsTable
from src.database.transactions.models import InvestmentTransaction, Transaction
from src.database.transactions.table import TransactionsTable
from src.database.users.models import User
from src.database.users.table import UsersTable
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class WalterDB:
    """
    WalterDB
    """

    ddb: WalterDDBClient
    authenticator: WalterAuthenticator
    domain: Domain

    # all tables created in post init
    users_table: UsersTable = None
    sessions_table: SessionsTable = None
    accounts_table: AccountsTable = None
    transactions_table: TransactionsTable = None
    securities_table: SecuritiesTable = None
    holdings_table: HoldingsTable = None

    def __post_init__(self) -> None:
        self.users_table = UsersTable(self.ddb, self.domain)
        self.sessions_table = SessionsTable(self.ddb, self.domain)
        self.accounts_table = AccountsTable(self.ddb, self.domain)
        self.transactions_table = TransactionsTable(self.ddb, self.domain)
        self.securities_table = SecuritiesTable(self.ddb, self.domain)
        self.holdings_table = HoldingsTable(self.ddb, self.domain)

    #########
    # USERS #
    #########

    def create_user(
        self, email: str, first_name: str, last_name: str, password: str
    ) -> User:
        # generate salt and hash the given password to store in users table
        salt, password_hash = self.authenticator.hash_secret(password)
        user = User(
            user_id=None,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password_hash=password_hash.decode(),
            sign_up_date=dt.datetime.now(dt.UTC),
            last_active_date=dt.datetime.now(dt.UTC),
        )
        return self.users_table.create_user(user)

    def get_user_by_id(self, user_id: str) -> User:
        return self.users_table.get_user_by_id(user_id)

    def get_user_by_email(self, email: str) -> User:
        return self.users_table.get_user_by_email(email)

    def get_users(self) -> List[User]:
        return self.users_table.get_users()

    def update_user(self, user: User) -> None:
        self.users_table.update_user(user)

    def update_user_password(self, email: str, password_hash: str) -> None:
        user = self.users_table.get_user_by_email(email)
        user.password_hash = password_hash.decode()
        self.users_table.update_user(user)

    def verify_user(self, user: User) -> None:
        user.verified = True
        self.users_table.update_user(user)

    def delete_user(self, email: str) -> None:
        self.users_table.delete_user(email)

    ############
    # SESSIONS #
    ############

    def create_session(
        self, user_id: str, token_id: str, ip_address: str, device: str
    ) -> Session:
        return self.sessions_table.create_session(user_id, token_id, ip_address, device)

    def get_session(self, user_id: str, token_id: str) -> Optional[Session]:
        return self.sessions_table.get_session(user_id, token_id)

    def update_session(self, session: Session) -> Session:
        return self.sessions_table.update_session(session)

    ################
    # TRANSACTIONS #
    ################

    def add_transaction(self, transaction: Transaction) -> Transaction:
        return self.transactions_table.put_transaction(transaction)

    def get_transaction(
        self, account_id: str, transaction_id: str, transaction_date: dt.datetime
    ) -> Optional[Transaction]:
        return self.transactions_table.get_transaction(
            account_id, transaction_date, transaction_id
        )

    def get_transactions_by_account(
        self,
        account_id: str,
        start_date: dt.datetime = dt.datetime.min,
        end_date: dt.datetime = dt.datetime.max,
    ) -> List[Transaction]:
        return self.transactions_table.get_transactions(
            account_id, start_date, end_date
        )

    def get_transactions_by_holding(
        self, account_id: str, security_id: str
    ) -> List[InvestmentTransaction]:
        log.info(
            f"Getting transactions for holding '{security_id}' in account '{account_id}'"
        )
        transactions = self.transactions_table.get_transactions(account_id)

        log.info(
            f"Found {len(transactions)} transactions in account '{account_id}'! Filtering transactions for holding '{security_id}'"
        )
        holding_transactions = []
        for transaction in transactions:
            if isinstance(transaction, InvestmentTransaction):
                if transaction.security_id == security_id:
                    holding_transactions.append(transaction)

        log.info(
            f"Found {len(holding_transactions)} transactions for holding '{security_id}' in account '{account_id}'"
        )

        return holding_transactions

    def get_user_transaction(
        self, user_id: str, transaction_id: str, transaction_date: dt.datetime
    ) -> Optional[Transaction]:
        return self.transactions_table.get_user_transaction(
            user_id, transaction_id, transaction_date
        )

    def get_transactions_by_user(
        self, user_id: str, start_date: dt.datetime, end_date: dt.datetime
    ) -> List[Transaction]:
        return self.transactions_table.get_user_transactions(
            user_id, start_date, end_date
        )

    def update_transaction(self, transaction: Transaction) -> Transaction:
        return self.transactions_table.put_transaction(transaction)

    def delete_transaction(
        self, account_id: str, transaction_id: str, date: dt.datetime
    ) -> None:
        return self.transactions_table.delete_transaction(
            account_id, date, transaction_id
        )

    def delete_account_transactions(self, account_id: str) -> None:
        transactions = self.transactions_table.get_transactions_by_account(account_id)
        for transaction in transactions:
            self.transactions_table.delete_transaction(
                account_id,
                transaction.get_transaction_date(),
                transaction.transaction_id,
            )

    ############
    # ACCOUNTS #
    ############

    def create_account(
        self,
        user_id: str,
        account_type: str,
        account_subtype: str,
        institution_name: str,
        account_name: str,
        account_mask: str,
        balance: float,
    ) -> Account:
        return self.accounts_table.create_account(
            user_id,
            account_type,
            account_subtype,
            institution_name,
            account_name,
            account_mask,
            balance,
        )

    def get_account(self, user_id: str, account_id: str) -> Optional[Account]:
        return self.accounts_table.get_account(user_id, account_id)

    def get_accounts(self, user_id: str) -> List[Account]:
        return self.accounts_table.get_accounts(user_id)

    def update_account(self, account: Account) -> Account:
        return self.accounts_table.update_account(account)

    def delete_account(self, user_id: str, account_id: str) -> None:
        return self.accounts_table.delete_account(user_id, account_id)

    ##############
    # SECURITIES #
    ##############

    def create_security(self, security: Security) -> Security:
        return self.securities_table.create_security(security)

    def get_security(self, security_id: str) -> Optional[Security]:
        return self.securities_table.get_security(security_id)

    def get_security_by_ticker(self, ticker: str) -> Optional[Security]:
        return self.securities_table.get_security_by_ticker(ticker)

    def get_securities(self) -> List[Security]:
        return self.securities_table.get_securities()

    def update_security(self, security: Security) -> Security:
        return self.securities_table.update_security(security)

    def put_security(self, security: Security) -> Security:
        return self.securities_table.update_security(security)

    ############
    # HOLDINGS #
    ############

    def get_holding(self, account_id: str, security_id: str) -> Optional[Holding]:
        return self.holdings_table.get_holding(account_id, security_id)

    def get_holdings(self, account_id: str) -> List[Holding]:
        return self.holdings_table.get_holdings(account_id)

    def put_holding(self, holding: Holding) -> Holding:
        return self.holdings_table.create_holding(holding)

    def delete_holding(self, account_id: str, security_id: str) -> None:
        return self.holdings_table.delete_holding(account_id, security_id)

    def delete_account_holdings(self, account_id: str) -> None:
        holdings = self.holdings_table.get_holdings(account_id)
        for holding in holdings:
            self.holdings_table.delete_holding(account_id, holding.security_id)
