import json
from dataclasses import dataclass

from src.events.models import CreateNewsletterAndSendEvent
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class WalterEventParser:
    """
    WalterEventParser
    """

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
        log.info(f"Parsing event:\n{json.dumps(event, indent=4)}")

        records = event["Records"]
        if len(records) != 1:
            raise ValueError("More than one record in event!")

        record = records[0]
        receipt_handle = record["receiptHandle"]
        body = json.loads(record["body"])

        return CreateNewsletterAndSendEvent(
            receipt_handle=receipt_handle,
            email=body["email"],
        )
