from dataclasses import dataclass


@dataclass
class Stock:
    """
    The model class for a Stock.

    Stock objects are stored in the Stocks table and the primary key for these
    objects is the symbol of the stock. All additional fields contained in this
    model class are additional metadata about the stock itself.
    """

    symbol: str
    company: str
    exchange: str = "N/A"
    sector: str = "N/A"
    industry: str = "N/A"
    description: str = "N/A"
    official_site: str = "N/A"
    address: str = "N/A"
    icon_url: str = "N/A"
    logo_url: str = "N/A"

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
            "exchange": {"S": self.exchange},
            "sector": {"S": self.sector},
            "industry": {"S": self.industry},
            "description": {"S": self.description},
            "official_site": {"S": self.official_site},
            "address": {"S": self.address},
            "icon_url": {"S": self.icon_url},
            "logo_url": {"S": self.logo_url},
        }

    def to_dict(self) -> dict:
        """
        Converts the Stock object into a dictionary of key-value pairs of the fields
        contained in this model class.

        Returns:
            The dict of fields and their values for a Stock object.
        """
        return {
            "symbol": self.symbol,
            "company": self.company,
            "exchange": self.exchange,
            "sector": self.sector,
            "industry": self.industry,
            "description": self.description,
            "official_site": self.official_site,
            "address": self.address,
            "icon_url": self.icon_url,
            "logo_url": self.logo_url,
        }
