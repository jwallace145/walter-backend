from dataclasses import dataclass


@dataclass(frozen=True)
class CompanyOverview:
    """
    Company Overview

    The model object for the AlphaVantage GetCompanyOverview API.
    """

    symbol: str
    name: str
    description: str
    exchange: str
    sector: str
    industry: str
    official_site: str

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "description": self.description,
            "exchange": self.exchange,
            "sector": self.sector,
            "industry": self.industry,
            "official_site": self.official_site,
        }
