import json

from src.api.exceptions import UserDoesNotExist, InvalidPassword, InvalidEmail
from src.api.methods import WalterAPIMethod, HTTPStatus, Status, is_valid_email
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.utils.log import Logger

log = Logger(__name__).get_logger()


class AuthUser(WalterAPIMethod):
    API_NAME = "AuthUser"
    REQUIRED_FIELDS = ["email", "password"]
    EXCEPTIONS = [UserDoesNotExist, InvalidPassword, InvalidEmail]

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
        walter_sm: WalterSecretsManagerClient,
    ) -> None:
        super().__init__(
            AuthUser.API_NAME,
            AuthUser.REQUIRED_FIELDS,
            AuthUser.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.walter_sm = walter_sm

    def execute(self, event: dict, authenticated_email: str = None) -> dict:
        body = json.loads(event["body"])

        email = body["email"]
        user = self.walter_db.get_user(email)
        if user is None:
            raise UserDoesNotExist("User not found!")

        password = body["password"]
        if not self.authenticator.check_password(password, user.password_hash):
            raise InvalidPassword("Password incorrect!")

        token = self.authenticator.generate_token(email)

        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="User authenticated!",
            data={"token": token},
        )

    def validate_fields(self, event: dict) -> None:
        body = json.loads(event["body"])

        email = body["email"]
        if not is_valid_email(email):
            raise InvalidEmail("Invalid email!")

    def is_authenticated_api(self) -> bool:
        return False
