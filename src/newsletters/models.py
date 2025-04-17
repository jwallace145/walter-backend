from dataclasses import dataclass

from src.templates.models import SupportedTemplate
import datetime as dt


@dataclass(frozen=True)
class NewsletterMetadata:

    DATE_FORMAT = "%Y-%m-%d"

    title: str
    date: dt.datetime
    model: str
    template: SupportedTemplate

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "date": self.date.strftime(self.DATE_FORMAT),
            "model": self.model,
            "template": self.template.name,
        }


@dataclass(frozen=True)
class Newsletter:

    DATE_FORMAT = "%Y-%m-%d"

    s3_uri: str
    title: str
    template: SupportedTemplate
    date: dt.datetime

    def to_dict(self) -> dict:
        return {
            "s3_uri": self.s3_uri,
            "title": self.title,
            "template": self.template.name,
            "date": self.date.strftime(Newsletter.DATE_FORMAT),
        }
