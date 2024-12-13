from dataclasses import dataclass

from src.api.common.exceptions import (
    InvalidEmail,
    BadRequest,
    UserDoesNotExist,
    EmailAlreadyVerified,
)
from src.api.common.methods import WalterAPIMethod, HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.ses.client import WalterSESClient
from src.database.client import WalterDB
from src.database.users.models import User
from src.templates.bucket import TemplatesBucket
from src.templates.engine import TemplatesEngine
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class SendVerifyEmail(WalterAPIMethod):
    """
    WalterAPI - SendVerifyEmail
    """

    API_NAME = "SendVerifyEmail"
    REQUIRED_HEADERS = {"Authorization": "Bearer"}
    REQUIRED_FIELDS = []
    EXCEPTIONS = [BadRequest, InvalidEmail, UserDoesNotExist, EmailAlreadyVerified]

    walter_db: WalterDB
    walter_ses: WalterSESClient
    templates_engine: TemplatesEngine
    templates_bucket: TemplatesBucket

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
            SendVerifyEmail.REQUIRED_HEADERS,
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
        user = self._verify_user_exists(authenticated_email)
        self._verify_user_not_already_verified(user)
        self._generate_and_send_verify_email(user)
        return self._create_response(
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Successfully sent verify email!",
        )

    def validate_fields(self, event: dict) -> None:
        pass  # no payload

    def is_authenticated_api(self) -> bool:
        return True

    def _verify_user_exists(self, email: str) -> User:
        log.info(f"Verifying user exists with email: '{email}'")
        user = self.walter_db.get_user(email)
        if user is None:
            raise UserDoesNotExist("User does not exist!")
        log.info("Verified user exists!")
        return user

    def _verify_user_not_already_verified(self, user: User) -> None:
        log.info(f"Verifying user email is not already verified: '{user.email}'")
        if user.verified:
            raise EmailAlreadyVerified("Email already verified!")
        log.info("Verified user email is not already verified!")

    def _generate_and_send_verify_email(self, user: User) -> None:
        log.info(f"Generate verify email template for user: '{user.email}'")
        token, url = self._get_verify_email_url(user.email)
        verify_email_template = self.templates_engine.get_template(
            template_name="verify",
            template_args={
                "User": user.username,
                "Url": url,
            },
        )
        log.info("Generated verify template successfully!")

        log.info(f"Sending verify email template to user: '{user.email}'")
        self.walter_ses.send_email(
            recipient=user.email,
            body=verify_email_template,
            subject="Walter: Verify your email!",
            assets=self.templates_bucket.get_template_assets(template="verify"),
        )
        log.info("Successfully sent verify email to user!")

    def _get_verify_email_url(self, email: str) -> str:
        verify_email_token = self.authenticator.generate_email_token(email)
        return (
            verify_email_token,
            f"https://www.walterai.dev/verify?token={verify_email_token}",
        )
