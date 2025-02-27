from dataclasses import dataclass

from stripe.checkout import Session

from src.api.common.exceptions import NotAuthenticated, UserDoesNotExist
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
import stripe

from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class PurchaseNewsletterSubscription(WalterAPIMethod):
    """
    WalterAPI: PurchaseNewsletterSubscription

    This API is used to create a Stripe checkout session where
    the user can enter their payment information to subscribe to
    Walter's newsletter.
    """

    API_NAME = "PurchaseNewsletterSubscription"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer"}
    REQUIRED_FIELDS = []
    EXCEPTIONS = [NotAuthenticated, UserDoesNotExist]

    walter_sm: WalterSecretsManagerClient

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
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
        self.walter_sm = walter_sm

    def execute(self, event: dict, authenticated_email: str = None) -> dict:
        self._set_stripe_api_key()
        checkout_session = self._create_checkout_session()
        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Checkout session created!",
            data={
                "checkout_session_id": checkout_session.id,
            },
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True

    def _set_stripe_api_key(self) -> None:
        if stripe.api_key is None:
            # TODO: Stop using Stripe test secret key when ready to start accepting payments
            stripe.api_key = self.walter_sm.get_stripe_test_secret_key()

    def _create_checkout_session(self) -> Session:
        log.info("Creating checkout session...")
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": "T-shirt",
                        },
                        "unit_amount": 2000,  # Price in cents ($20.00)
                    },
                    "quantity": 1,
                },
            ],
            mode="payment",
            success_url="https://walterai.dev/login",
            cancel_url="https://walterai.dev/register",
        )
        log.info("Successfully created checkout session!")
        return session
