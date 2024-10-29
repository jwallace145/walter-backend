from src.api.exceptions import UserDoesNotExist, InvalidToken
from src.api.methods import WalterAPIMethod
from src.api.models import HTTPStatus, Status
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB


class GetUser(WalterAPIMethod):
    API_NAME = "GetUser"
    REQUIRED_FIELDS = []
    EXCEPTIONS = [InvalidToken, UserDoesNotExist]

    def __init__(
        self,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
        walter_sm: WalterSecretsManagerClient,
    ) -> None:
        super().__init__(
            GetUser.API_NAME, GetUser.REQUIRED_FIELDS, GetUser.EXCEPTIONS, walter_cw
        )
        self.walter_db = walter_db
        self.walter_sm = walter_sm

    def execute(self, event: dict, authenticated_email: str) -> dict:
        user = self.walter_db.get_user(authenticated_email)
        if user is None:
            raise UserDoesNotExist("User does not exist!")

        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Successfully retrieved user!",
            data={"user": authenticated_email},
        )

    def validate_fields(self, event: dict) -> None:
        pass  # no payload for get user requests

    def is_authenticated_api(self) -> bool:
        return True

    def get_jwt_secret_key(self) -> str:
        return self.walter_sm.get_jwt_secret_key()
