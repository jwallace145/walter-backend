from dataclasses import dataclass
from typing import List

from src.aws.dynamodb.client import WalterDDBClient
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
    domain: Domain

    users_table: UsersTable = None
    stocks_table: StocksTable = None
    users_stocks_table: UsersStocksTable = None

    def __post_init__(self) -> None:
        self.users_table = UsersTable(self.ddb, self.domain)
        self.stocks_table = StocksTable(self.ddb, self.domain)
        self.users_stocks_table = UsersStocksTable(self.ddb, self.domain)

    def get_user(self, email: str) -> User:
        return self.users_table.get_user(email)

    def get_stocks_for_user(self, user: User) -> List[UserStock]:
        return self.users_stocks_table.get_stocks_for_user(user)
