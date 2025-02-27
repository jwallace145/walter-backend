from dataclasses import dataclass
from enum import Enum

from src.api.common.exceptions import (
    NotAuthenticated,
    UserDoesNotExist,
    UnknownPaymentStatus,
)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
import stripe

from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.database.users.models import User
from src.utils.log import Logger

log = Logger(__name__).get_logger()

#############
# CONSTANTS #
#############


class PaymentStatus(Enum):
    """
    The possible payment statuses for Stripe checkout sessions.
    """

    PAID = "paid"
    UNPAID = "unpaid"
    PENDING = "pending"


@dataclass
class VerifyPurchaseNewsletterSubscription(WalterAPIMethod):
    """
    WalterAPI: VerifyPurchaseNewsletterSubscription

    This API is used to verify newsletter subscription purchases made
    through Stripe via the session ID. For context, users can purchase
    a newsletter subscription through a Stripe checkout session. On
    success or failure, Stripe redirects the user to a Walter webpage
    with the session ID token in the URL. The session ID token is used
    to check the status of the user payment against Stripe and verify
    the payment was successful before enabling subscription. This ensures
    no one gets a free newsletter unless intended :)
    """

    API_NAME = "VerifyPurchaseNewsletterSubscription"
    REQUIRED_QUERY_FIELDS = ["sessionId"]
    REQUIRED_HEADERS = {"Authorization": "Bearer"}
    REQUIRED_FIELDS = []
    EXCEPTIONS = [NotAuthenticated, UserDoesNotExist, UnknownPaymentStatus]

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
            VerifyPurchaseNewsletterSubscription.API_NAME,
            VerifyPurchaseNewsletterSubscription.REQUIRED_QUERY_FIELDS,
            VerifyPurchaseNewsletterSubscription.REQUIRED_HEADERS,
            VerifyPurchaseNewsletterSubscription.REQUIRED_FIELDS,
            VerifyPurchaseNewsletterSubscription.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.walter_sm = walter_sm

    def execute(self, event: dict, authenticated_email: str = None) -> dict:
        user = self._verify_user_exists(authenticated_email)
        self._set_stripe_api_key()
        session_id = self._get_session_id(event)
        session = self._get_session(session_id)
        if session.payment_status == PaymentStatus.PAID.value:
            log.info("Checkout session has been paid!")
            user.subscribed = True
            user.stripe_subscription_id = session.subscription
            user.stripe_customer_id = session.customer
            self.walter_db.update_user(user)
            return self._create_response(
                http_status=HTTPStatus.OK,
                status=Status.SUCCESS,
                message="Checkout session has been paid!",
                data={
                    "customer_email": user.email,
                    "stripe_customer_id": user.stripe_customer_id,
                    "stripe_subscription_id": user.stripe_subscription_id,
                },
            )
        if session.payment_status == PaymentStatus.UNPAID.value:
            log.info("Checkout session has not been paid!")
            return self._create_response(
                http_status=HTTPStatus.OK,
                status=Status.FAILURE,
                message="Checkout session is unpaid!",
            )
        if session.payment_status == PaymentStatus.PENDING.value:
            log.info("Checkout session is pending payment!")
            return self._create_response(
                http_status=HTTPStatus.OK,
                status=Status.FAILURE,
                message="Checkout session is pending payment!",
            )
        raise UnknownPaymentStatus(
            f"Unknown payment status '{session.payment_status}'!"
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True

    def _verify_user_exists(self, authenticated_email: str) -> User:
        log.info(f"Verifying user exists: '{authenticated_email}'")
        user = self.walter_db.get_user(authenticated_email)
        if user is None:
            raise UserDoesNotExist("User does not exist!")
        log.info("Verified user exists!")
        return user

    def _set_stripe_api_key(self) -> None:
        if stripe.api_key is None:
            # TODO: Stop using Stripe test secret key when ready to start accepting payments
            stripe.api_key = self.walter_sm.get_stripe_test_secret_key()

    def _get_session_id(self, event: dict) -> str | None:
        return event["queryStringParameters"]["sessionId"]

    def _get_session(self, session_id: str) -> stripe.checkout.Session:
        log.info("Getting checkout session...")
        log.debug(f"Session ID: {session_id}")
        session = stripe.checkout.Session.retrieve(session_id)
        log.info("Successfully retrieved checkout session!")
        return session
