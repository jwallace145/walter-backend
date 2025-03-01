from dataclasses import dataclass

from src.api.common.exceptions import (
    NotAuthenticated,
    UserDoesNotExist,
    UnknownPaymentStatus,
)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.database.users.models import User
from src.payments.stripe.client import WalterStripeClient
from src.payments.stripe.models import PaymentStatus
from src.utils.log import Logger

log = Logger(__name__).get_logger()


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
    walter_payments: WalterStripeClient

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
        walter_sm: WalterSecretsManagerClient,
        walter_payments: WalterStripeClient,
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
        self.walter_payments = walter_payments

    def execute(self, event: dict, authenticated_email: str = None) -> dict:
        user = self._verify_user_exists(authenticated_email)
        session_id = self._get_session_id(event)
        session = self.walter_payments.get_session(session_id)
        payment_status = WalterStripeClient.get_payment_status(session.payment_status)
        if payment_status == PaymentStatus.PAID:
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
        if payment_status == PaymentStatus.UNPAID:
            log.info("Checkout session has not been paid!")
            return self._create_response(
                http_status=HTTPStatus.OK,
                status=Status.FAILURE,
                message="Checkout session is unpaid!",
            )
        if payment_status == PaymentStatus.PENDING:
            log.info("Checkout session is pending payment!")
            return self._create_response(
                http_status=HTTPStatus.OK,
                status=Status.FAILURE,
                message="Checkout session is pending payment!",
            )
        raise UnknownPaymentStatus(
            f"Unknown payment status '{payment_status}'!"
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

    def _get_session_id(self, event: dict) -> str | None:
        return event["queryStringParameters"]["sessionId"]
