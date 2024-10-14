from dataclasses import dataclass
from typing import Dict

from src.aws.dynamodb.client import WalterDDBClient
from src.database.stocks.table import StocksTable
from src.database.users.models import User
from src.database.users.table import UsersTable
from src.database.userstocks.models import UserStock
from src.database.userstocks.table import UsersStocksTable
from src.environment import Domain
from src.utils.auth import hash_password
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class WalterDB:

    ddb: WalterDDBClient
    domain: Domain

    users_table: UsersTable = None
    stocks_table: StocksTable = None
    users_stocks_table: UsersStocksTable = None

    def __post_init__(self) -> None:
        self.users_table = UsersTable(self.ddb, self.domain)
        self.stocks_table = StocksTable(self.ddb, self.domain)
        self.users_stocks_table = UsersStocksTable(self.ddb, self.domain)

    def create_user(self, email: str, username: str, password: str) -> None:
        # generate salt and hash the given password to store in users table
        salt, password_hash = hash_password(password)
        user = User(
            email=email,
            username=username,
            password_hash=password_hash.decode(),
            salt=salt.decode(),
        )
        self.users_table.create_user(user)

    def get_user(self, email: str) -> User:
        return self.users_table.get_user(email)

    def update_user(self, user: User) -> None:
        self.users_table.update_user(user)

    def delete_user(self, email: str) -> None:
        self.users_table.delete_user(email)

    def get_stocks_for_user(self, user: User) -> Dict[str, UserStock]:
        stocks = self.users_stocks_table.get_stocks_for_user(user)
        return {stock.stock_symbol: stock for stock in stocks}

    def add_stock_to_user_portfolio(self, stock: UserStock) -> None:
        self.users_stocks_table.add_stocks_to_user_portfolio(stock)
