import datetime as dt
from dataclasses import dataclass
from typing import List, Optional

from src.auth.authenticator import WalterAuthenticator
from src.aws.dynamodb.client import WalterDDBClient
from src.database.accounts.models import Account
from src.database.accounts.table import AccountsTable
from src.database.models import AccountTransaction
from src.database.plaid_items.model import PlaidItem
from src.database.plaid_items.table import PlaidItemsTable
from src.database.transactions.models import Transaction
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
    transactions_table: TransactionsTable = None
    users_table: UsersTable = None
    accounts_table: AccountsTable = None
    plaid_items_table: PlaidItemsTable = None

    def __post_init__(self) -> None:
        self.transactions_table = TransactionsTable(self.ddb, self.domain)
        self.users_table = UsersTable(self.ddb, self.domain)
        self.accounts_table = AccountsTable(self.ddb, self.domain)
        self.plaid_items_table = PlaidItemsTable(self.ddb, self.domain)

    #########
    # USERS #
    #########

    def create_user(
        self, email: str, first_name: str, last_name: str, password: str
    ) -> User:
        # generate salt and hash the given password to store in users table
        salt, password_hash = self.authenticator.hash_password(password)
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password_hash=password_hash.decode(),
            sign_up_date=dt.datetime.now(dt.UTC),
            last_active_date=dt.datetime.now(dt.UTC),
        )
        return self.users_table.create_user(user)

    def get_user(self, email: str) -> User:
        return self.users_table.get_user_by_email(email)

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

    ################
    # TRANSACTIONS #
    ################

    def get_transaction(
        self, user_id: str, date: dt.datetime, transaction_id: str
    ) -> Optional[Transaction]:
        """
        Gets a specific transaction for a given user on a specified date.

        This method retrieves a transaction entry from the Transactions table based
        on the provided user ID, transaction date, and transaction ID. If the transaction
        does not exist, it returns None.

        Args:
            user_id (str): The unique ID of the user that owns the transaction.
            date (datetime): The date of the specific transaction.
            transaction_id (str): The unique ID of the transaction.

        Returns:
            Optional[Transaction]: The transaction object if found; otherwise, None.
        """
        return self.transactions_table.get_transaction(user_id, date, transaction_id)

    def get_transactions(
        self, user_id: str, start_date: dt.datetime, end_date: dt.datetime
    ) -> List[AccountTransaction]:
        """
        Gets all transactions for the given user within a specified date range.

        This method retrieves transaction records for the given user over the
        provided data range by executing a query against the Transactions table.

        Args:
            user_id: The unique ID of the user that owns the returned transactions.
            start_date: The beginning of the date range for the user-owned transactions.
            end_date: The end of the date range for the user-owned transactions.

        Returns:
            The transactions for the given user within the specified date range.
        """
        # create account id to accounts dict
        accounts = {}
        for account in self.get_accounts(user_id):
            accounts[account.account_id] = account

        # get transactions owned by user over given date range
        transactions = self.transactions_table.get_transactions(
            user_id, start_date, end_date
        )

        # merge owning account with transaction before returning
        account_transactions = []
        for transaction in transactions:
            account_transactions.append(
                AccountTransaction(
                    account=accounts[transaction.account_id],
                    transaction=transaction,
                )
            )

        return account_transactions

    def put_transaction(self, transaction: Transaction) -> None:
        """
        This method updates or adds a transaction to the Transactions table.

        Note, if the user updates the date of a transaction, this method will
        delete the original transaction as transaction date is a part of the
        sort key and then recreate a new transaction with the updated date.
        This ensures duplicate entries are not created when users update
        the date of a transaction.

        Args:
            transaction: The transaction object to be added or updated.
        """
        self.transactions_table.put_transaction(transaction)

    def delete_transaction(
        self, user_id: str, date: dt.datetime, transaction_id: str
    ) -> None:
        """
        Deletes a transaction record from the Transactions table based on the specified
        user ID, date, and transaction ID.

        Args:
            user_id: The unique ID of the user that owns the transaction.
            date: The date of the transaction.
            transaction_id: The unique ID of the transaction.
        """
        self.transactions_table.delete_transaction(user_id, date, transaction_id)

    def delete_transactions(self, user_id: str, account_id: str) -> None:
        """
        Delete all transactions for a user and account_id.

        Args:
            user_id: The user that owns the account.
            account_id: The owning account of the transactions to delete.

        Returns:
            None.
        """
        # get all transactions for user and filter by account_id
        for transaction in self.get_transactions(
            user_id, dt.datetime.min, dt.datetime.max
        ):
            if transaction.account.account_id == account_id:
                self.delete_transaction(
                    user_id,
                    transaction.transaction.date,
                    transaction.transaction.transaction_id,
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

    ###############
    # PLAID ITEMS #
    ###############

    def get_plaid_item_by_item_id(self, item_id: str) -> Optional[PlaidItem]:
        return self.plaid_items_table.get_item_by_item_id(item_id)

    def get_plaid_items(self, user_id: str) -> List[PlaidItem]:
        return self.plaid_items_table.get_items(user_id)

    def put_plaid_item(self, item: PlaidItem) -> PlaidItem:
        return self.plaid_items_table.put_item(item)

    def delete_plaid_item(self, user_id: str, item_id: str) -> None:
        self.plaid_items_table.delete_item(user_id, item_id)
