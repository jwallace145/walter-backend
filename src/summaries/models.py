from dataclasses import dataclass
from datetime import datetime

from src.stocks.alphavantage.models import CompanyNews


@dataclass(frozen=True)
class NewsSummary:
    """
    NewsSummary
    """

    DATESTAMP_FORMAT = "%Y-%m-%d"

    stock: str
    datestamp: datetime
    model_name: str
    news: CompanyNews
    summary: str

    def get_metadata(self) -> dict:
        return {
            "model_name": self.model_name,
            "stock": self.stock,
            "datestamp": self.datestamp.strftime(NewsSummary.DATESTAMP_FORMAT),
            "news": self.news.to_dict(),
        }

    def get_summary(self) -> dict:
        return {
            "model_name": self.model_name,
            "stock": self.stock,
            "datestamp": self.datestamp.strftime(NewsSummary.DATESTAMP_FORMAT),
            "summary": self.summary,
        }
