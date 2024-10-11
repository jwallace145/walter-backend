import json
from dataclasses import dataclass

from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class Event:

    receipt_handle: str
    email: str

    def __str__(self) -> str:
        return json.dumps(
            {
                "receipt_handle": self.receipt_handle,
                "email": self.email,
            },
            indent=4,
        )


def parse_event(event: dict) -> Event:
    records = event["Records"]
    if len(records) != 1:
        raise ValueError("More than a single message found in an SQS batch!")

    record = records[0]
    receipt_handle = record["receiptHandle"]
    body = json.loads(record["body"])

    event = Event(receipt_handle=receipt_handle, email=body["email"])

    log.info(f"Parsed event: {event}")

    return event
