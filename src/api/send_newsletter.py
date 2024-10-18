import json
from dataclasses import dataclass

from src.api.exceptions import UserDoesNotExist, InvalidEmail
from src.api.models import HTTPStatus, Status, create_response
from src.api.utils import is_valid_email, authenticate_request
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.newsletters.queue import NewsletterRequest, NewslettersQueue
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class SendNewsletter:

    API_NAME = "WalterAPI: SendNewsletter"
    REQUIRED_FIELDS = ["email"]
    EXCEPTIONS = [InvalidEmail, UserDoesNotExist]

    walter_db: WalterDB
    newsletters_queue: NewslettersQueue
    walter_sm: WalterSecretsManagerClient

    def invoke(self, event: dict) -> dict:
        log.info(
            f"Sending newsletter to user with event: {json.dumps(event, indent=4)}"
        )

        if not self._is_valid_request(event):
            error_msg = "Client bad request to send newsletter!"
            log.error(error_msg)
            return create_response(
                SendNewsletter.API_NAME,
                HTTPStatus.BAD_REQUEST,
                Status.FAILURE,
                error_msg,
            )

        return self._send_newsletter(event)

    def _is_valid_request(self, event: dict) -> bool:
        body = json.loads(event["body"])
        for field in SendNewsletter.REQUIRED_FIELDS:
            if field not in body:
                return False
        return True

    def _send_newsletter(self, event: dict) -> dict:
        try:
            body = json.loads(event["body"])
            email = body["email"]

            if not is_valid_email(email):
                raise InvalidEmail("Invalid email!")

            user = self.walter_db.get_user(email)
            if user is None:
                raise UserDoesNotExist("User not found!")

            authenticate_request(event, self.walter_sm.get_jwt_secret_key())

            self.newsletters_queue.add_newsletter_request(NewsletterRequest(email))

            return create_response(
                SendNewsletter.API_NAME,
                HTTPStatus.OK,
                Status.SUCCESS,
                "Newsletter sent!",
            )
        except Exception as exception:
            status = HTTPStatus.INTERNAL_SERVER_ERROR
            for e in SendNewsletter.EXCEPTIONS:
                if isinstance(exception, e):
                    status = HTTPStatus.OK
                    break
            return create_response(
                SendNewsletter.API_NAME,
                status,
                Status.FAILURE,
                str(exception),
            )
