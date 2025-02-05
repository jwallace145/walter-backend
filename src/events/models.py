import datetime as dt
from dataclasses import dataclass


@dataclass(frozen=True)
class CreateNewsletterAndSendEvent:
    """
    CreateNewsletterAndSendEvent

    This event is consumed by WalterBackend via a SQS queue and is used
    to generate and send a newsletter to a user with the given email.
    """

    receipt_handle: str
    email: str


@dataclass(frozen=True)
class CreateNewsSummaryAndArchiveEvent:
    """
    CreateNewsSummaryAndArchiveEvent

    This event is consumed by a WalterWorkflow via a SQS queue and is used
    for asynchronous generation of stock news summaries. After generation,
    the summary is archived for use by WalterFrontend and WalterAPI.
    """

    receipt_handle: str
    datestamp: dt.datetime
    stock: str
