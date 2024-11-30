from src.api.common.exceptions import NotAuthenticated, UserDoesNotExist
from src.api.common.methods import WalterAPIMethod, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB


class Unsubscribe(WalterAPIMethod):
    """
    WalterAPI - Unsubscribe
    """

    API_NAME = "Unsubscribe"
    REQUIRED_FIELDS = []
    EXCEPTIONS = [NotAuthenticated, UserDoesNotExist]

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            Unsubscribe.API_NAME,
            Unsubscribe.REQUIRED_FIELDS,
            Unsubscribe.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str) -> dict:
        user = self.walter_db.get_user(authenticated_email)
        if user is None:
            raise UserDoesNotExist("User does not exist!")

        user.subscribed = False
        self.walter_db.update_user(user)

        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Unsubscribed user!",
        )

    def validate_fields(self, event: dict) -> None:
        pass  # no payload for get user requests

    def is_authenticated_api(self) -> bool:
        return True
