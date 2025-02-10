from dataclasses import dataclass
from typing import List

from src.stocks.alphavantage.models import NewsArticle


@dataclass(frozen=True)
class NewsSummary:
    """
    NewsSummary
    """

    stock: str
    model_name: str
    articles: List[NewsArticle]
    summary: str

    def to_dict(self) -> dict:
        return {
            "stock": self.stock,
            "model_name": self.model_name,
            "articles": [article.to_dict() for article in self.articles],
            "summary": self.summary,
        }
