from typing import Tuple

from src.api.common.exceptions import BadRequest, UserDoesNotExist
from src.api.common.methods import WalterAPIMethod, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.ses.client import WalterSESClient
from src.database.client import WalterDB
from src.templates.bucket import TemplatesBucket
from src.templates.engine import TemplatesEngine


class SendChangePasswordEmail(WalterAPIMethod):

    API_NAME = "SendChangePasswordEmail"
    REQUIRED_QUERY_FIELDS = ["email"]
    REQUIRED_FIELDS = []
    EXCEPTIONS = [BadRequest, UserDoesNotExist]

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
        walter_ses: WalterSESClient,
        templates_engine: TemplatesEngine,
        templates_bucket: TemplatesBucket,
    ) -> None:
        super().__init__(
            SendChangePasswordEmail.API_NAME,
            SendChangePasswordEmail.REQUIRED_FIELDS,
            SendChangePasswordEmail.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.walter_ses = walter_ses
        self.templates_engine = templates_engine
        self.templates_bucket = templates_bucket

    def execute(self, event: dict, authenticated_email: str = None) -> dict:
        # get email from query parameters
        email = self._get_email(event)

        # verify user exists with email
        user = self.walter_db.get_user(email)
        if user is None:
            raise UserDoesNotExist("User does not exist!")

        # create change password template
        token, url = self._get_change_password_url(email)
        change_password_template = self.templates_engine.get_template(
            template_name="change_password",
            template_args={
                "User": user.username,
                "Url": url,
            },
        )

        # send verify email template to user
        self.walter_ses.send_email(
            recipient=user.email,
            body=change_password_template,
            subject="Walter: Change your password!",
            assets=self.templates_bucket.get_template_assets(
                template="change_password"
            ),
        )

        # return success response
        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Successfully sent change password email!",
        )

    def validate_fields(self, event: dict) -> None:
        query_parameters = event.get("queryStringParameters", {})

        if query_parameters is None:
            raise BadRequest(
                f"Client bad request! Missing required query parameters: {SendChangePasswordEmail.REQUIRED_QUERY_FIELDS}"
            )

        for field in SendChangePasswordEmail.REQUIRED_QUERY_FIELDS:
            if field not in query_parameters:
                raise BadRequest(
                    f"Client bad request! Missing required query parameter: '{field}'"
                )

    def is_authenticated_api(self) -> bool:
        return False

    def _get_email(self, event: dict) -> str | None:
        return event["queryStringParameters"]["email"]

    def _get_change_password_url(self, email: str) -> Tuple[str, str]:
        change_password_token = self.authenticator.generate_change_password_token(email)
        return (
            change_password_token,
            f"https://www.walterai.dev/password?token={change_password_token}",
        )
