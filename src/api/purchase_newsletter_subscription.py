from dataclasses import dataclass

import stripe

from src.api.common.exceptions import (
    NotAuthenticated,
    UserDoesNotExist,
    EmailNotVerified,
    EmailAlreadySubscribed,
)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.config import CONFIG
from src.database.client import WalterDB
from src.database.users.models import User
from src.utils.log import Logger

log = Logger(__name__).get_logger()

#############
# CONSTANTS #
#############

PRODUCT_NAME = "Walter's Weekly Newsletter"
"""(str): The name of the product, this is what is shown on the checkout page."""

PRODUCT_DESCRIPTION = "Stay informed with Walter's curated newsletter, powered by AI, delivering insightful updates and recommendations tailored for your portfolio each week."
"""(str): The description of the product, this is what is shown on the checkout page."""


@dataclass
class PurchaseNewsletterSubscription(WalterAPIMethod):
    """
    WalterAPI: PurchaseNewsletterSubscription

    This API is used to create a Stripe checkout session where
    the user can enter their payment information to subscribe to
    Walter's newsletter.
    """

    # TODO: Implement these pages via WalterFrontend then change these
    SUCCESS_URL = "https://walterai.dev/newsletter/purchase/success?sessionId={CHECKOUT_SESSION_ID}"
    CANCEL_URL = "https://walterai.dev/register?sessionId={CHECKOUT_SESSION_ID}"

    API_NAME = "PurchaseNewsletterSubscription"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer"}
    REQUIRED_FIELDS = []
    EXCEPTIONS = [
        NotAuthenticated,
        UserDoesNotExist,
        EmailNotVerified,
        EmailAlreadySubscribed,
    ]

    walter_db: WalterDB
    walter_sm: WalterSecretsManagerClient

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
        walter_sm: WalterSecretsManagerClient,
    ) -> None:
        super().__init__(
            PurchaseNewsletterSubscription.API_NAME,
            PurchaseNewsletterSubscription.REQUIRED_QUERY_FIELDS,
            PurchaseNewsletterSubscription.REQUIRED_HEADERS,
            PurchaseNewsletterSubscription.REQUIRED_FIELDS,
            PurchaseNewsletterSubscription.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.walter_sm = walter_sm

    def execute(self, event: dict, authenticated_email: str = None) -> dict:
        user = self._verify_user_exists(authenticated_email)
        self._verify_user_email_verified(user)
        self._verify_user_not_already_subscribed(user)
        self._set_stripe_api_key()
        checkout_session = self._create_checkout_session()
        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Checkout session created!",
            data={
                "customer_email": authenticated_email,
                "stripe_checkout_session_id": checkout_session.id,
                "stripe_checkout_url": checkout_session.url,
            },
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True

    def _verify_user_exists(self, email: str) -> User:
        log.info(f"Verifying user exists: '{email}'")
        user = self.walter_db.get_user(email)
        if user is None:
            raise UserDoesNotExist("User does not exist!")
        log.info("Verified user exists!")
        return user

    def _verify_user_email_verified(self, user: User) -> None:
        log.info(f"Verifying user email is verified: '{user.email}'")
        if not user.verified:
            raise EmailNotVerified("Email not verified!")
        log.info("User email is verified!")

    def _verify_user_not_already_subscribed(self, user: User) -> None:
        log.info(f"Verifying user is not already subscribed: '{user.email}'")
        if user.stripe_subscription_id:
            raise EmailAlreadySubscribed("User is already subscribed!")
        log.info("User is not already subscribed!")

    def _set_stripe_api_key(self) -> None:
        if stripe.api_key is None:
            # TODO: Stop using Stripe test secret key when ready to start accepting payments
            stripe.api_key = self.walter_sm.get_stripe_test_secret_key()

    def _create_checkout_session(self) -> stripe.checkout.Session:
        log.info("Creating checkout session...")
        newsletter_subscription = self._create_newsletter_subscription_offering()
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[newsletter_subscription],
            mode="subscription",
            success_url=PurchaseNewsletterSubscription.SUCCESS_URL,
            cancel_url=PurchaseNewsletterSubscription.CANCEL_URL,
        )
        log.info("Successfully created checkout session!")
        return session

    def _create_newsletter_subscription_offering(
        self, price_in_cents: int = CONFIG.newsletter.cents_per_month
    ) -> dict:
        return {
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": PRODUCT_NAME,
                    "description": PRODUCT_DESCRIPTION,
                },
                "recurring": {"interval": "month"},
                "unit_amount": price_in_cents,
            },
            "quantity": 1,
        }
