import pytest

from src.events.parser import WalterEventParser, CreateNewsletterAndSendEvent
from tst.events.utils import get_walter_backend_event

EMAIL = "walter@gmail.com"
EVENT = get_walter_backend_event(email=EMAIL)
PARSED_EVENT = CreateNewsletterAndSendEvent(
    receipt_handle="test-receipt-handle", email=EMAIL
)


@pytest.fixture
def walter_event_parser() -> WalterEventParser:
    return WalterEventParser()


def test_parse_create_newsletter_and_send_event(
    walter_event_parser: WalterEventParser,
) -> None:
    PARSED_EVENT == walter_event_parser.parse_create_newsletter_and_send_event(EVENT)
