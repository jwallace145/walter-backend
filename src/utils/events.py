import json
from dataclasses import dataclass

from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class Event:
    email: str
    dry_run: bool = True

    def __str__(self) -> str:
        return json.dumps(
            {
                "email": self.email,
                "dry_run": self.dry_run,
            },
            indent=4,
        )


def parse_event(event: dict) -> Event:
    records = event["Records"]
    if len(records) != 1:
        raise ValueError("More than a single message found in an SQS batch!")

    body = json.loads(records[0]["body"])
    event = Event(email=body["email"], dry_run=body["dry_run"])

    log.info(f"Parsed event: {event}")

    return event
