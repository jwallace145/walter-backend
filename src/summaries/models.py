from dataclasses import dataclass
from typing import List
from datetime import datetime

from src.stocks.alphavantage.models import NewsArticle


@dataclass(frozen=True)
class NewsSummary:
    """
    NewsSummary
    """

    DATESTAMP_FORMAT = "%Y-%m-%d"

    stock: str
    datestamp: datetime
    model_name: str
    articles: List[NewsArticle]
    summary: str

    def get_metadata(self) -> dict:
        return {
            "model_name": self.model_name,
            "stock": self.stock,
            "datestamp": self.datestamp.strftime(NewsSummary.DATESTAMP_FORMAT),
            "articles": [article.to_dict() for article in self.articles],
        }

    def get_summary(self) -> dict:
        return {
            "model_name": self.model_name,
            "stock": self.stock,
            "datestamp": self.datestamp.strftime(NewsSummary.DATESTAMP_FORMAT),
            "summary": self.summary,
        }
