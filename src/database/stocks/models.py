from dataclasses import dataclass


@dataclass(frozen=True)
class Stock:
    """
    The model class for a Stock.

    Stock objects are stored in the Stocks table and the primary key for these
    objects is the symbol of the stock. All additional fields contained in this
    model class are additional metadata about the stock itself.
    """

    symbol: str
    company: str

    def to_ddb_item(self) -> dict:
        """
        Converts the Stock object to a DDB item to be easily inserted into the
        Stocks table.

        Returns:
            The Stock object as a DDB item.
        """
        return {
            "symbol": {
                "S": self.symbol,
            },
            "company": {"S": self.company},
        }
