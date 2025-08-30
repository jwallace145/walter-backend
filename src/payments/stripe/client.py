from dataclasses import dataclass

import stripe
from stripe.checkout import Session

from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.config import CONFIG
from src.payments.stripe.exceptions import InvalidPaymentStatus
from src.payments.stripe.models import NewsletterSubscriptionOffering, PaymentStatus
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class WalterStripeClient:
    """
    Stripe Client

    The Walter client responsible for interacting with Stripe
    for newsletter subscription purchases.
    """

    walter_sm: WalterSecretsManagerClient

    # lazy init
    stripe_api_key: str = None

    def __post_init__(self):
        log.debug("Initializing WalterStripeClient")
        # TODO: Add config to switch between test Stripe key and prod Stripe key

    def create_checkout_session(self, success_url: str, cancel_url: str) -> Session:
        log.info("Creating checkout session...")
        newsletter_subscription = (
            WalterStripeClient.get_newsletter_subscription_offering(
                CONFIG.newsletter.cents_per_month
            )
        )
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[newsletter_subscription],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
        )
        log.info("Successfully created checkout session!")
        return session

    def get_session(self, session_id: str) -> Session:
        log.info("Getting checkout session...")
        log.debug(f"Session ID: '{session_id}'")
        session = stripe.checkout.Session.retrieve(session_id)
        log.info("Successfully retrieved checkout session!")
        return session

    def _lazily_load_client(self) -> None:
        if self.stripe_api_key is None:
            # TODO: Don't use the test key
            self.stripe_api_key = self.walter_sm.get_stripe_test_secret_key()

    @staticmethod
    def get_newsletter_subscription_offering(
        cents_per_month: int = CONFIG.newsletter.cents_per_month,
    ) -> dict:
        return NewsletterSubscriptionOffering(cents_per_month=cents_per_month).to_dict()

    @staticmethod
    def get_payment_status(payment_status: str) -> PaymentStatus:
        for status in PaymentStatus:
            if status.value == payment_status:
                return status
        raise InvalidPaymentStatus(f"Invalid payment status: '{payment_status}'!")
