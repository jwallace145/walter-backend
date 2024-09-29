from dataclasses import dataclass
from typing import List

from src.database.client import WalterDDBClient
from src.database.users.models import User
from src.database.userstocks.models import UserStock
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class UsersStocksTable:
    """
    UsersStocks Table

    This table maintains mappings from users to stocks to store
    user portfolios.

    Item Schema
    - user_email (HASH key): The primary key of the user.
    - stock_symbol (RANGE key): The primary key of the stock.
    - quantity: The quantity of the stock owned by the user.
    """

    TABLE_NAME_FORMAT = "UsersStocks-{domain}"

    ddb: WalterDDBClient
    domain: Domain

    table: str = None  # set during post init

    def __post_init__(self) -> None:
        self.table = UsersStocksTable._get_table_name(self.domain)
        log.debug(f"Creating UsersStocks table DDB client for table '{self.table}'")

    def get_stocks_for_user(self, user: User) -> List[UserStock]:
        """
        Get the stocks owned by a user.

        Args:
            user: The user to get the stocks.

        Returns:
            The stocks owned by the user.
        """
        log.info(f"Getting stocks for user '{user.email}' from table '{self.table}'")
        stocks = []
        for item in self.ddb.query(
            self.table, UsersStocksTable._get_user_stocks_query_key(user.email)
        ):
            stocks.append(UsersStocksTable._get_user_stock_from_ddb_item(item))
        log.info(f"Returned {len(stocks)} stocks for user '{user.email}'")
        return stocks

    @staticmethod
    def _get_table_name(domain: Domain) -> str:
        return UsersStocksTable.TABLE_NAME_FORMAT.format(domain=domain.value)

    @staticmethod
    def _get_user_stocks_query_key(user_email: str) -> dict:
        return {
            "user_email": {
                "AttributeValueList": [{"S": user_email}],
                "ComparisonOperator": "EQ",
            }
        }

    @staticmethod
    def _get_user_stock_from_ddb_item(item: dict) -> UserStock:
        return UserStock(
            user_email=item["user_email"]["S"],
            stock_symbol=item["stock_symbol"]["S"],
            quantity=float(item["quantity"]["N"]),
        )