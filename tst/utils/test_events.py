from src.utils.events import parse_event, Event
from tst.utils.utils import get_walter_backend_event

EVENT = get_walter_backend_event("walter@gmail.com")

PARSED_EVENT = Event(receipt_handle="test-receipt-handle", email="walter@gmail.com")


def test_parse_event() -> None:
    assert PARSED_EVENT == parse_event(EVENT)
