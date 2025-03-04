import datetime
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class CompanyStatistics:
    """
    Company Statistics
    """

    market_cap: int
    ebitda: int
    pe_ratio: float
    dividend_yield: float
    eps: float
    fifty_two_week_high: float
    fifty_two_week_low: float

    def to_dict(self) -> dict:
        return {
            "market_cap": self.market_cap,
            "ebitda": self.ebitda,
            "pe_ratio": self.pe_ratio,
            "dividend_yield": self.dividend_yield,
            "eps": self.eps,
            "fifty_two_week_high": self.fifty_two_week_high,
            "fifty_two_week_low": self.fifty_two_week_low,
        }


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
    published_timestamp: datetime.datetime
    authors: List[str]
    source: str
    summary: str
    contents: str

    def get_metadata(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "published_timestamp": self.published_timestamp.strftime("%Y-%m-%d"),
            "authors": self.authors,
            "source": self.source,
            "summary": self.summary,
        }

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "published_timestamp": self.published_timestamp.strftime("%Y-%m-%d"),
            "authors": self.authors,
            "source": self.source,
            "summary": self.summary,
            "contents": self.contents,
        }


@dataclass(frozen=True)
class CompanyNews:
    """
    Company News
    """

    stock: str
    company: str
    start_date: datetime.datetime
    end_date: datetime.datetime
    articles: List[NewsArticle]

    def to_dict(self) -> dict:
        return {
            "stock": self.stock,
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "end_date": self.end_date.strftime("%Y-%m-%d"),
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
