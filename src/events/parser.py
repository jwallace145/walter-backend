import json
from dataclasses import dataclass

from src.events.models import (
    CreateNewsletterAndSendEvent,
    CreateNewsSummaryAndArchiveEvent,
)
from src.utils.log import Logger
import datetime as dt

log = Logger(__name__).get_logger()


@dataclass
class WalterEventParser:
    """
    WalterEventParser
    """

    def parse_create_news_summary_and_archive_event(
        self, event: dict
    ) -> CreateNewsSummaryAndArchiveEvent:
        """
        Parse NewsSummaries queue SQS message into CreateNewsSummaryAndArchiveEvent.

        Args:
            event: The NewsSummaries SQS message to parse.

        Returns:
            The NewsSummaries message as CreateNewsSummaryAndArchiveEvent.
        """
        log.info("Parsing CreateNewsSummaryAndArchive event...")
        log.debug(f"Event:\n{json.dumps(event, indent=4)}")

        WalterEventParser.verify_one_record(event)
        records = event["Records"]
        record = records[0]
        receipt_handle = record["receiptHandle"]
        body = json.loads(record["body"])

        return CreateNewsSummaryAndArchiveEvent(
            receipt_handle=receipt_handle,
            datestamp=dt.datetime.strptime(body["datestamp"], "%Y-%m-%d"),
            stock=body["stock"],
        )

    def parse_create_newsletter_and_send_event(
        self, event: dict
    ) -> CreateNewsletterAndSendEvent:
        """
        Parse SQS event into a CreateNewsletterAndSendEvent event to be consumed by WalterBackend.

        Args:
            event: The SQS event consumed by WalterBackend.

        Returns:
            The SQS event as a CreateNewsletterAndSendEvent event.
        """
        log.info("Parsing CreateNewsletterAndSend event...")
        log.debug(f"Event:\n{json.dumps(event, indent=4)}")

        WalterEventParser.verify_one_record(event)
        records = event["Records"]
        record = records[0]
        receipt_handle = record["receiptHandle"]
        body = json.loads(record["body"])

        log.info(f"Parsed CreateNewsletterAndSend event for email: '{body['email']}'")

        return CreateNewsletterAndSendEvent(
            receipt_handle=receipt_handle,
            email=body["email"],
        )

    @staticmethod
    def verify_one_record(event: dict) -> None:
        records = event["Records"]
        if len(records) != 1:
            raise ValueError("More than one record in event!")
