import json
from dataclasses import dataclass

from src.api.models import HTTPStatus, Status, create_response
from src.newsletters.queue import NewsletterRequest, NewslettersQueue
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class SendNewsletter:

    API_NAME = "WalterAPI: SendNewsletter"
    REQUIRED_FIELDS = ["email"]

    newsletters_queue: NewslettersQueue

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
        for field in SendNewsletter.REQUIRED_FIELDS:
            if field not in event:
                return False
        return True

    def _send_newsletter(self, event: dict) -> dict:
        try:
            request = NewsletterRequest(email=json.loads(event["body"]))
            self.newsletters_queue.add_newsletter_request(request)
            return create_response(
                SendNewsletter.API_NAME,
                HTTPStatus.OK,
                Status.SUCCESS,
                "Newsletter sent!",
            )
        except Exception as exception:
            return create_response(
                SendNewsletter.API_NAME,
                HTTPStatus.INTERNAL_SERVER_ERROR,
                Status.FAILURE,
                str(exception),
            )
