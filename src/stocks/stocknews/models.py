from dataclasses import dataclass
from typing import List
from datetime import datetime


@dataclass(frozen=True)
class StockNewsArticle:
    """
    StockNewsArticle

    The StockNewsArticle model object for news articles
    returned by StockNews API.
    """

    news_url: str
    image_url: str
    title: str
    text: str
    contents: str
    source: str
    published_timestamp: datetime


@dataclass(frozen=True)
class StockNews:
    """
    StockNews

    The StockNews model object for news related to
    a given stock returned by StockNews API.
    """

    stock: str
    start_date: datetime
    end_date: datetime
    articles: List[StockNewsArticle]
