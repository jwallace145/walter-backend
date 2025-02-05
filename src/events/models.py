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
