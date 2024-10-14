import json
from dataclasses import dataclass

from src.api.models import HTTPStatus, Status, Response
from src.clients import newsletters_queue
from src.newsletters.queue import NewsletterRequest
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class SendNewsletter:

    API_NAME = "WalterAPI: SendNewsletter"
    REQUIRED_FIELDS = ["email"]

    event: dict

    def invoke(self) -> dict:
        log.info(
            f"Sending newsletter to user with event: {json.dumps(self.event, indent=4)}"
        )

        if not self._is_valid_request():
            error_msg = "Client bad request to send newsletter!"
            log.error(error_msg)
            return self._create_response(
                HTTPStatus.BAD_REQUEST, Status.FAILURE, error_msg
            )

        return self._send_newsletter()

    def _is_valid_request(self) -> bool:
        for field in SendNewsletter.REQUIRED_FIELDS:
            if field not in self.event:
                return False
        return True

    def _send_newsletter(self) -> dict:
        try:
            request = NewsletterRequest(email=json.loads(self.event["body"]))
            newsletters_queue.send_newsletter(request)
            return self._create_response(
                HTTPStatus.OK, Status.SUCCESS, "Newsletter sent!"
            )
        except Exception as exception:
            return self._create_response(
                HTTPStatus.INTERNAL_SERVER_ERROR, Status.FAILURE, str(exception)
            )

    def _create_response(
        self, http_status: HTTPStatus, status: Status, message: str
    ) -> dict:
        return Response(
            api_name=SendNewsletter.API_NAME,
            http_status=http_status,
            status=status,
            message=message,
        ).to_json()
