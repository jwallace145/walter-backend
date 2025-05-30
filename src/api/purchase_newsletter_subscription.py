from dataclasses import dataclass

from src.api.common.exceptions import (
    NotAuthenticated,
    UserDoesNotExist,
    EmailNotVerified,
    EmailAlreadySubscribed,
)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Status, Response
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.database.users.models import User
from src.payments.stripe.client import WalterStripeClient
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
        self.walter_payments = walter_payments

    def execute(self, event: dict, authenticated_email: str = None) -> Response:
        user = self._verify_user_exists(authenticated_email)
        self._verify_user_email_verified(user)
        self._verify_user_not_already_subscribed(user)
        checkout_session = self.walter_payments.create_checkout_session(
            success_url=PurchaseNewsletterSubscription.SUCCESS_URL,
            cancel_url=PurchaseNewsletterSubscription.CANCEL_URL,
        )
        return Response(
            api_name=PurchaseNewsletterSubscription.API_NAME,
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
