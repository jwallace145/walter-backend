from dataclasses import dataclass
from typing import List

from src.database.client import WalterDDBClient
from src.database.stocks.models import Stock
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class StocksTable:
    """
    Stocks Table

    This table contains all the unique stocks owned by Walter subscribers
    and maintains additional metadata about the stocks.

    Item Schema:
        - symbol (str): The symbol of the stock, e.g. AAPL.
        - company (str): The company name of the stock, e.g. Apple.
    """

    STOCKS_TABLE_NAME_FORMAT = "Stocks-{domain}"

    ddb: WalterDDBClient
    domain: Domain

    table: str = None  # set during post init

    def __post_init__(self) -> None:
        self.table = StocksTable._get_stocks_table_name(self.domain)
        log.debug(f"Creating StocksTable DDB client with table name '{self.table}'")

    def get_stock(self, symbol: str) -> Stock:
        """
        Gets a Stock from the Stocks table.

        Args:
            symbol: The symbol of the Stock to query the Stocks table.

        Returns:
            The Stock object if it exists in the Stocks table.
        """
        log.info(f"Getting stock with symbol '{symbol}' from table '{self.table}'")
        key = StocksTable._get_stock_key(symbol)
        item = self.ddb.get_item(self.table, key)
        return StocksTable._get_stock_from_ddb_item(item) if item is not None else None

    def list_stocks(self) -> List[Stock]:
        """
        Lists all stocks in the Stocks table.

        This is an expensive operation as it simply scans the entire table.
        Use this method with caution.

        Returns:
            The list of all Stocks included in the Stocks table.
        """
        log.info(f"Listing all stocks in table '{self.table}'")
        return [
            StocksTable._get_stock_from_ddb_item(item)
            for item in self.ddb.scan_table(self.table)
        ]

    def put_stock(self, stock: Stock) -> None:
        """
        Puts a Stock into the Stocks table.

        Args:
            stock: The Stock object to insert into the Stocks table.

        Returns:
            None.
        """
        log.info(f"Putting stock '{stock}' to table '{self.table}'")
        self.ddb.put_item(self.table, stock.to_ddb_item())

    @staticmethod
    def _get_stocks_table_name(domain: Domain) -> str:
        """
        Returns the table name for the Stocks table.

        Args:
            domain: The domain of the Stocks table.

        Returns:
            The table name for the Stocks table.
        """
        return StocksTable.STOCKS_TABLE_NAME_FORMAT.format(domain=domain.value)

    @staticmethod
    def _get_stock_key(symbol: str) -> dict:
        """
        Returns primary key for a stock to query the Stocks table.

        Args:
            symbol: The symbol of the stock to query the Stocks table.

        Returns:
            The primary key for the stock.
        """
        return {"symbol": {"S": symbol}}

    @staticmethod
    def _get_stock_from_ddb_item(item: dict) -> Stock:
        """
        Returns a Stock object from the Stocks table response.

        Args:
            item: The response from the Stocks table.

        Returns:
            The Stock object from the Stocks table.
        """
        return Stock(symbol=item["symbol"]["S"], company=item["company"]["S"])
