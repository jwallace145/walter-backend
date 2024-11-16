from src.api.exceptions import (
    NotAuthenticated,
    InvalidEmail,
    BadRequest,
    UserDoesNotExist,
)
from src.api.methods import WalterAPIMethod, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.ses.client import WalterSESClient
from src.database.client import WalterDB
from src.templates.bucket import TemplatesBucket
from src.templates.engine import TemplatesEngine


class SendVerifyEmail(WalterAPIMethod):

    API_NAME = "SendVerifyEmail"
    REQUIRED_FIELDS = []
    EXCEPTIONS = [BadRequest, NotAuthenticated, InvalidEmail, UserDoesNotExist]

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
            SendVerifyEmail.API_NAME,
            SendVerifyEmail.REQUIRED_FIELDS,
            SendVerifyEmail.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.walter_ses = walter_ses
        self.templates_engine = templates_engine
        self.templates_bucket = templates_bucket

    def execute(self, event: dict, authenticated_email: str) -> dict:
        # verify user exists
        user = self.walter_db.get_user(authenticated_email)
        if user is None:
            raise UserDoesNotExist("User does not exist!")

        # create verify email template with email verification token
        token, url = self._get_verify_email_url(user.email)
        verify_email_template = self.templates_engine.get_template(
            template_name="verify",
            template_args={
                "User": user.username,
                "Url": url,
            },
        )

        # send verify email template to user
        self.walter_ses.send_email(
            recipient=user.email,
            body=verify_email_template,
            subject="Walter: Verify your email!",
            assets=self.templates_bucket.get_template_assets(template="verify"),
        )

        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Successfully sent verify email!",
            data={"token": token},
        )

    def validate_fields(self, event: dict) -> None:
        pass  # no payload

    def is_authenticated_api(self) -> bool:
        return True

    def _get_verify_email_url(self, email: str) -> str:
        verify_email_token = self.authenticator.generate_email_token(email)
        return (
            verify_email_token,
            f"https://www.walterai.dev/verify?token={verify_email_token}",
        )
