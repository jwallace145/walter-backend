from dataclasses import dataclass
from typing import List

from mypy_boto3_dynamodb import DynamoDBClient
from src.environment import Domain
from src.utils.log import Logger
from src.dynamodb.models import User, Stock, UserStock

log = Logger(__name__).get_logger()


@dataclass
class DDBClient:
    """
    Walter AI DynamoDB Client

    Tables:
        - Stocks-{domain}
        - Users-{domain}
        - UsersStocks-{domain}
    """

    STOCKS_TABLE_NAME_FORMAT = "Stocks-{domain}"
    USERS_TABLE_NAME_FORMAT = "Users-{domain}"
    USERS_STOCKS_TABLE_NAME_FORMAT = "UsersStocks-{domain}"

    client: DynamoDBClient
    domain: Domain

    stocks_table: str = None
    users_table: str = None
    users_stocks_table: str = None

    def __post_init__(self) -> None:
        log.debug(
            f"Creating {self.domain.value} DDB client in region '{self.client.meta.region_name}'"
        )
        self.stocks_table = self._get_stocks_table_name()
        self.users_table = self._get_users_table_name()
        self.users_stocks_table = self._get_users_stocks_table_name()

    def put_stock(self, stock: Stock) -> None:
        log.info(f"Adding stock '{stock}' to table '{self.stocks_table}'")
        self.client.put_item(TableName=self.stocks_table, Item=stock.to_ddb_item())

    def put_user(self, user: User) -> None:
        log.info(f"Adding user '{user}' to table '{self.users_table}'")
        self.client.put_item(TableName=self.users_table, Item=user.to_ddb_item())

    def get_users(self) -> List[User]:
        log.info(f"Getting users from table '{self.users_table}'")
        users = [
            DDBClient._get_user_from_ddb_item(item)
            for item in self.client.scan(TableName=self.users_table)["Items"]
        ]
        log.info(f"Returned {len(users)} user(s) from table '{self.users_table}'")
        return users

    def put_user_stock(self, user: User, stock: Stock) -> None:
        self.put_user(user)
        self.put_stock(stock)
        user_stock = UserStock(user.email, stock.symbol)
        log.info(
            f"Adding user stock '{user_stock}' to table '{self.users_stocks_table}'"
        )
        self.client.put_item(
            TableName=self.users_stocks_table, Item=user_stock.to_ddb_item()
        )

    def get_stocks_for_user(self, user: User) -> List[Stock]:
        log.info(
            f"Getting stocks for user '{user}' from table '{self.users_stocks_table}'"
        )
        user_stocks = [
            DDBClient._get_user_stock_from_ddb_item(item)
            for item in self.client.query(
                TableName=self.users_stocks_table,
                KeyConditions=DDBClient._get_user_stocks_query_key(user.email),
            )["Items"]
        ]
        stocks = [self.get_stock(user_stock.stock_symbol) for user_stock in user_stocks]
        log.info(f"Returned {len(stocks)} stocks for user '{user}'")
        return stocks

    def get_stock(self, symbol: str) -> Stock:
        log.info(
            f"Getting stock with symbol '{symbol}' from table '{self.stocks_table}'"
        )
        stock = DDBClient._get_stock_from_ddb_item(
            self.client.get_item(
                TableName=self.stocks_table, Key=DDBClient._get_stock_key(symbol)
            )["Item"]
        )
        log.info(f"Returned stock '{stock}' from table '{self.stocks_table}'")
        return stock

    def get_stocks(self) -> List[Stock]:
        log.info(f"Getting stocks from table '{self.stocks_table}'")
        stocks = [
            DDBClient._get_stock_from_ddb_item(item)
            for item in self.client.scan(TableName=self.stocks_table)["Items"]
        ]
        log.info(f"Returned {len(stocks)} stock(s) from table '{self.stocks_table}'")
        return stocks

    def _get_stocks_table_name(self) -> str:
        return DDBClient.STOCKS_TABLE_NAME_FORMAT.format(domain=self.domain.value)

    def _get_users_table_name(self) -> str:
        return DDBClient.USERS_TABLE_NAME_FORMAT.format(domain=self.domain.value)

    def _get_users_stocks_table_name(self) -> str:
        return DDBClient.USERS_STOCKS_TABLE_NAME_FORMAT.format(domain=self.domain.value)

    @staticmethod
    def _get_user_stocks_query_key(user_email: str) -> dict:
        return {
            "user_email": {
                "AttributeValueList": [{"S": user_email}],
                "ComparisonOperator": "EQ",
            }
        }

    @staticmethod
    def _get_stock_key(symbol: str) -> dict:
        return {"symbol": {"S": symbol}}

    @staticmethod
    def _get_stock_from_ddb_item(item: dict) -> Stock:
        print(item)
        return Stock(symbol=item["symbol"]["S"], company=item["company"]["S"])

    @staticmethod
    def _get_user_from_ddb_item(item: dict) -> User:
        return User(email=item["email"]["S"], username=item["username"]["S"])

    @staticmethod
    def _get_user_stock_from_ddb_item(item: dict) -> UserStock:
        print(item)
        return UserStock(
            user_email=item["user_email"]["S"], stock_symbol=item["stock_symbol"]["S"]
        )
