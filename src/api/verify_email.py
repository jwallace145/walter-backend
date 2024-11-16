from src.api.exceptions import BadRequest, NotAuthenticated
from src.api.methods import WalterAPIMethod, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB


class VerifyEmail(WalterAPIMethod):

    API_NAME = "VerifyEmail"
    REQUIRED_FIELDS = []
    EXCEPTIONS = [BadRequest, NotAuthenticated]

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            VerifyEmail.API_NAME,
            VerifyEmail.REQUIRED_FIELDS,
            VerifyEmail.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str = None) -> dict:
        token = self.authenticator.get_token(event)
        if token is None:
            raise NotAuthenticated("Not authenticated!")

        decoded_token = self.authenticator.decode_email_token(token)
        if decoded_token is None:
            raise NotAuthenticated("Not authenticated!")

        user = self.walter_db.get_user(email=decoded_token["sub"])
        self.walter_db.verify_user(user)

        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Successfully verified email!",
        )

    def validate_fields(self, event: dict) -> None:
        pass  # no payload

    def is_authenticated_api(self) -> bool:
        return False
