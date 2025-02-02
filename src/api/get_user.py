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

    API_NAME = "GetUser"
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
            },
        )

    def validate_fields(self, event: dict) -> None:
        pass  # no payload for get user requests

    def is_authenticated_api(self) -> bool:
        return True
