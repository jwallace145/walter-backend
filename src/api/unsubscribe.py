from dataclasses import dataclass

from src.api.common.exceptions import (
    NotAuthenticated,
    UserDoesNotExist,
    EmailAlreadyUnsubscribed,
)
import stripe
from src.api.common.methods import WalterAPIMethod, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.database.users.models import User
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class Unsubscribe(WalterAPIMethod):
    """
    WalterAPI - Unsubscribe
    """

    API_NAME = "Unsubscribe"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer"}
    REQUIRED_FIELDS = []
    EXCEPTIONS = [NotAuthenticated, UserDoesNotExist, EmailAlreadyUnsubscribed]

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
            Unsubscribe.API_NAME,
            Unsubscribe.REQUIRED_QUERY_FIELDS,
            Unsubscribe.REQUIRED_HEADERS,
            Unsubscribe.REQUIRED_FIELDS,
            Unsubscribe.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.walter_sm = walter_sm

    def execute(self, event: dict, authenticated_email: str) -> dict:
        user = self._verify_user_exists(authenticated_email)
        self._verify_user_is_not_already_unsubscribed(user)
        self._set_stripe_api_key()
        self._unsubscribe_user(user)
        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Unsubscribed user!",
        )

    def validate_fields(self, event: dict) -> None:
        pass  # no payload for get user requests

    def is_authenticated_api(self) -> bool:
        return True

    def _verify_user_exists(self, email: str) -> User:
        log.info(f"Verifying user exists with email: '{email}'")
        user = self.walter_db.get_user(email)
        if user is None:
            raise UserDoesNotExist("User does not exist!")
        log.info("Verified user exists!")
        return user

    def _verify_user_is_not_already_unsubscribed(self, user: User) -> None:
        log.info(f"Verifying user is not already unsubscribed: '{user.email}'")
        if not user.subscribed:
            raise EmailAlreadyUnsubscribed("Email is already unsubscribed!")
        log.info("Verified user is not already unsubscribed!")

    def _set_stripe_api_key(self) -> None:
        if stripe.api_key is None:
            # TODO: Stop using Stripe test secret key when ready to start accepting payments
            stripe.api_key = self.walter_sm.get_stripe_test_secret_key()

    def _unsubscribe_user(self, user: User) -> None:
        log.info(f"Unsubscribing user from newsletter with email: '{user.email}'")

        # set user subscription status to false, this is separate from Stripe subscription
        user.subscribed = False

        # check if user has active Stripe subscription and cancel it if found
        # user does not have active subscription during free trial but subscribe status is set to true
        if user.stripe_subscription_id is not None:
            log.info("User has active Stripe subscription!")
            customer_id = user.stripe_customer_id
            subscription_id = user.stripe_subscription_id

            log.info(f"Retrieving Stripe subscription with ID: '{subscription_id}'")
            subscription = stripe.Subscription.retrieve(subscription_id)

            if subscription.customer == customer_id:
                log.info("Deleting Stripe subscription...")
                stripe.Subscription.delete(subscription)
                user.stripe_subscription_id = None
                user.stripe_customer_id = None
                log.info(f"Successfully deleted Stripe subscription for user: '{user.email}'")
            else:
                log.error("Not deleting Stripe subscription! Customer IDs do not match!")

        self.walter_db.update_user(user)
        log.info("Successfully unsubscribed user from newsletter!")
