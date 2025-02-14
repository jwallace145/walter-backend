import datetime
from dataclasses import dataclass
from typing import List


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
class NewsArticle:
    """
    News Article

    The model object for a news article from AlphaVantage.
    """

    title: str
    url: str
    contents: str

    def to_dict(self) -> dict:
        return {"title": self.title, "url": self.url, "summary": self.contents}


@dataclass(frozen=True)
class CompanyNews:
    """
    Company News
    """

    stock: str
    datestamp: datetime.datetime
    articles: List[NewsArticle]

    def to_dict(self) -> dict:
        return {
            "stock": self.stock,
            "datestamp": self.datestamp.strftime("%Y-%m-%d"),
            "articles": [article.to_dict() for article in self.articles],
        }

    def get_article_urls(self) -> List[str]:
        return [article.url for article in self.articles]


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
