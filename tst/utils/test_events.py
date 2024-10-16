import json

from src.utils.events import parse_event, Event

EVENT = json.load(open("tst/utils/data/event.json"))

PARSED_EVENT = Event(receipt_handle="test-receipt-handle", email="walter@gmail.com")


def test_parse_event() -> None:
    assert PARSED_EVENT == parse_event(EVENT)
