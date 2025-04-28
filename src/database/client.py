import datetime as dt
from dataclasses import dataclass
from typing import Dict, List

from src.auth.authenticator import WalterAuthenticator
from src.aws.dynamodb.client import WalterDDBClient
from src.database.expenses.models import Expense
from src.database.expenses.table import ExpensesTable
from src.database.stocks.models import Stock
from src.database.stocks.table import StocksTable
from src.database.users.models import User
from src.database.users.table import UsersTable
from src.database.userstocks.models import UserStock
from src.database.userstocks.table import UsersStocksTable
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class WalterDB:

    ddb: WalterDDBClient
    authenticator: WalterAuthenticator
    domain: Domain

    expenses_table: ExpensesTable = None
    users_table: UsersTable = None
    stocks_table: StocksTable = None
    users_stocks_table: UsersStocksTable = None

    def __post_init__(self) -> None:
        self.expenses_table = ExpensesTable(self.ddb, self.domain)
        self.users_table = UsersTable(self.ddb, self.domain)
        self.stocks_table = StocksTable(self.ddb, self.domain)
        self.users_stocks_table = UsersStocksTable(self.ddb, self.domain)

    def create_user(
        self, email: str, first_name: str, last_name: str, password: str
    ) -> None:
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
        self.users_table.create_user(user)

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

    def get_stock(self, symbol: str) -> Stock | None:
        """
        Get stock by symbol from WalterDB, return None if not found.

        Args:
            symbol: The stock ticker symbol.

        Returns:
            The stock details from WalterDB or None if not found.
        """
        return self.stocks_table.get_stock(symbol)

    def add_stock(self, stock: Stock) -> None:
        self.stocks_table.put_stock(stock)

    def get_all_stocks(self) -> List[Stock]:
        """
        Get all stocks from WalterDB.

        Returns:
            The list of all stocks stored in WalterDB.
        """
        return self.stocks_table.get_stocks()

    def get_stocks(self, symbols: List[str]) -> Dict[str, Stock]:
        stocks = [self.get_stock(symbol) for symbol in symbols]
        return {stock.symbol: stock for stock in stocks}

    def get_stocks_for_user(self, user: User) -> Dict[str, UserStock]:
        stocks = self.users_stocks_table.get_stocks_for_user(user)
        return {stock.stock_symbol: stock for stock in stocks}

    def add_stock_to_user_portfolio(self, stock: UserStock) -> None:
        self.users_stocks_table.add_stocks_to_user_portfolio(stock)

    def delete_stock_from_user_portfolio(self, stock: UserStock) -> None:
        self.users_stocks_table.delete_stock_from_user_portfolio(stock)

    ############
    # EXPENSES #
    ############

    def get_expenses(
        self, user_email: str, start_date: dt.datetime, end_date: dt.datetime
    ) -> List[Expense]:
        return self.expenses_table.get_expenses(user_email, start_date, end_date)

    def put_expense(self, expense: Expense) -> None:
        self.expenses_table.put_expense(expense)

    def delete_expense(
        self, user_email: str, date: dt.datetime, expense_id: str
    ) -> None:
        self.expenses_table.delete_expense(user_email, date, expense_id)
