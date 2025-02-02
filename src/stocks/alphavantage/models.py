from dataclasses import dataclass
from typing import Dict


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
    address: str

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "description": self.description,
            "exchange": self.exchange,
            "sector": self.sector,
            "industry": self.industry,
            "official_site": self.official_site,
            "address": self.address,
        }


@dataclass(frozen=True)
class CompanyNews:
    """
    Company News
    """

    symbol: str
    news: Dict[str, str]

    def to_dict(self) -> dict:
        return {"symbol": self.symbol, "news": self.news}


@dataclass(frozen=True)
class CompanySearch:
    """
    Company Search
    """

    symbol: str
    name: str
    type: str
    region: str
    currency: str
    match_score: float

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "type": self.type,
            "region": self.region,
            "currency": self.currency,
            "match_score": self.match_score,
        }
