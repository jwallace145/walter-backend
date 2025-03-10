import datetime as dt
from dataclasses import dataclass

from src.api.common.exceptions import UserDoesNotExist, NotAuthenticated
from src.api.common.methods import HTTPStatus, Status
from src.api.common.methods import WalterAPIMethod
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB


@dataclass
class GetUser(WalterAPIMethod):
    """
    WalterAPI - GetUser
    """

    DATE_FORMAT = "%Y-%m-%d"

    API_NAME = "GetUser"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer"}
    REQUIRED_FIELDS = []
    EXCEPTIONS = [NotAuthenticated, UserDoesNotExist]

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
            GetUser.API_NAME,
            GetUser.REQUIRED_QUERY_FIELDS,
            GetUser.REQUIRED_HEADERS,
            GetUser.REQUIRED_FIELDS,
            GetUser.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.walter_sm = walter_sm

    def execute(self, event: dict, authenticated_email: str) -> dict:
        user = self.walter_db.get_user(authenticated_email)
        if user is None:
            raise UserDoesNotExist("User does not exist!")

        # update user last active date
        user.last_active_date = dt.datetime.now(dt.UTC)
        self.walter_db.update_user(user)

        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Successfully retrieved user!",
            data={
                "email": authenticated_email,
                "username": user.username,
                "verified": user.verified,
                "subscribed": user.subscribed,
                "sign_up_date": user.sign_up_date.strftime(GetUser.DATE_FORMAT),
                "last_active_date": user.last_active_date.strftime(GetUser.DATE_FORMAT),
                "free_trial_end_date": user.free_trial_end_date.strftime(
                    GetUser.DATE_FORMAT
                ),
                "stripe_customer_id": (
                    "N/A" if not user.stripe_customer_id else user.stripe_customer_id
                ),
                "stripe_subscription_id": (
                    "N/A"
                    if not user.stripe_subscription_id
                    else user.stripe_subscription_id
                ),
            },
        )

    def validate_fields(self, event: dict) -> None:
        pass  # no payload for get user requests

    def is_authenticated_api(self) -> bool:
        return True
