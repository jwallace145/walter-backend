import json
from dataclasses import dataclass

from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class Event:
    email: str

    def __str__(self) -> str:
        return json.dumps(
            {
                "email": self.email,
            },
            indent=4,
        )


def parse_event(event: dict) -> Event:
    records = event["Records"]
    if len(records) != 1:
        raise ValueError("More than a single message found in an SQS batch!")

    return Event(email=json.loads(records[0]["body"])["email"])
