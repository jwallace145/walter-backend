from dataclasses import dataclass
from typing import List

from src.dynamodb.client import WalterDDBClient
from src.dynamodb.stocks.models import Stock
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class StocksTable:
    """
    Stocks Table

    Item Schema:
        - symbol (str)
        - company (str)
    """

    STOCKS_TABLE_NAME_FORMAT = "Stocks-{domain}"

    ddb: WalterDDBClient
    domain: Domain

    table: str = None  # set during post init

    def __post_init__(self) -> None:
        self.table = StocksTable._get_stocks_table_name(self.domain)
        log.debug(f"Creating StocksTable DDB client with table name '{self.table}'")

    def get_stock(self, symbol: str) -> Stock:
        log.info(f"Getting stock with symbol '{symbol}' from table '{self.table}'")
        key = StocksTable._get_stock_key(symbol)
        item = self.ddb.get_item(self.table, key)
        return StocksTable._get_stock_from_ddb_item(item)

    def list_stocks(self) -> List[Stock]:
        log.info(f"Listing stocks from table '{self.table}'")
        stocks = []
        for item in self.ddb.scan_table(self.table):
            stocks.append(StocksTable._get_stock_from_ddb_item(item))
        return stocks

    def put_stock(self, stock: Stock) -> None:
        log.info(f"Putting stock '{stock}' to table '{self.table}'")
        self.ddb.put_item(self.table, stock.to_ddb_item())

    @staticmethod
    def _get_stocks_table_name(domain: Domain) -> str:
        return StocksTable.STOCKS_TABLE_NAME_FORMAT.format(domain=domain.value)

    @staticmethod
    def _get_stock_key(symbol: str) -> dict:
        return {"symbol": {"S": symbol}}

    @staticmethod
    def _get_stock_from_ddb_item(item: dict) -> Stock:
        return Stock(symbol=item["symbol"]["S"], company=item["company"]["S"])
