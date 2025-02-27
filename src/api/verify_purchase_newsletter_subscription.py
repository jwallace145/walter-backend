from dataclasses import dataclass

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
    EXCEPTIONS = [NotAuthenticated, UserDoesNotExist]

    walter_sm: WalterSecretsManagerClient

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
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
        self.walter_sm = walter_sm

    def execute(self, event: dict, authenticated_email: str = None) -> dict:
        self._set_stripe_api_key()
        session_id = self._get_session_id(event)
        status = self._get_payment_status(session_id)
        if status == "paid":
            return self._create_response(
                http_status=HTTPStatus.OK,
                status=Status.SUCCESS,
                message="Payment verified!",
            )
        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.FAILURE,
            message="Payment not verified!",
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True

    def _set_stripe_api_key(self) -> None:
        if stripe.api_key is None:
            # TODO: Stop using Stripe test secret key when ready to start accepting payments
            stripe.api_key = self.walter_sm.get_stripe_test_secret_key()

    def _get_session_id(self, event: dict) -> str | None:
        return event["queryStringParameters"]["sessionId"]

    def _get_payment_status(self, session_id: str) -> str:
        log.info("Getting payment status of session...")
        log.debug(f"Session ID: {session_id}")
        session = stripe.checkout.Session.retrieve(session_id)
        payment_status = session.payment_status
        log.info(f"Payment status of '{payment_status}' retrieved!")
        return payment_status
