import json
from dataclasses import dataclass

from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class Event:

    email: str
    dry_run: bool

    def __str__(self) -> str:
        return json.dumps(
            {
                "email": self.email,
                "dry_run": self.dry_run,
            },
            indent=4,
        )


def get_dry_run(body: dict) -> bool:
    if body["dry_run"].lower() == "true":
        return True
    return False


def parse_event(event: dict) -> Event:
    records = event["Records"]
    if len(records) != 1:
        raise ValueError("More than a single message found in an SQS batch!")

    body = json.loads(records[0]["body"])
    event = Event(email=body["email"], dry_run=get_dry_run(body))

    log.info(f"Parsed event: {event}")

    return event
