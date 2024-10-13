import json
from enum import Enum

from src.clients import walter_db, newsletters_queue
from src.database.users.models import User
from src.database.userstocks.models import UserStock
from src.newsletters.queue import NewsletterRequest
from src.utils.log import Logger

log = Logger(__name__).get_logger()


class Status(Enum):
    SUCCESS = "Success"
    FAILURE = "Failure"


class HTTPStatus(Enum):
    OK = 200
    BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR = 500


########
# APIS #
########

CREATE_USERS_API_NAME = "CreateUser"
ADD_STOCK_API_NAME = "AddStock"
SEND_NEWSLETTER_API_NAME = "SendNewsletter"

############
# HANDLERS #
############


def create_user(event, context) -> dict:
    log.info(f"Creating user with event: {json.dumps(event, indent=4)}")

    user = None
    try:
        body = json.loads(event["body"])
        user = User(email=body["email"], username=body["username"])
    except Exception as exception:
        log.error("Client bad request to create user!", exception)
        return {
            "statusCode": HTTPStatus.BAD_REQUEST.value,
            "body": json.dumps(
                {
                    "API": CREATE_USERS_API_NAME,
                    "Status": Status.FAILURE.value,
                }
            ),
        }

    try:
        walter_db.create_user(user)
        return {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps(
                {
                    "API": CREATE_USERS_API_NAME,
                    "Status": Status.SUCCESS.value,
                    "User": str(user),
                }
            ),
        }
    except Exception as exception:
        log.error("Unexpected error occurred attempting to create user!", exception)
        return {
            "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR.value,
            "body": json.dumps(
                {"API": CREATE_USERS_API_NAME, "Status": Status.FAILURE.value}
            ),
        }


def add_stock(event, context) -> dict:
    log.info(
        f"Adding stock to user portfolio with event: {json.dumps(event, indent=4)}"
    )

    stock = None
    try:
        body = json.loads(event["body"])
        stock = UserStock(
            user_email=body["email"],
            stock_symbol=body["stock"],
            quantity=body["quantity"],
        )
    except Exception as exception:
        log.error("Client bad request to add stock to user portfolio!", exception)
        return {
            "statusCode": HTTPStatus.BAD_REQUEST.value,
            "body": json.dumps(
                {
                    "API": ADD_STOCK_API_NAME,
                    "Status": Status.FAILURE.value,
                }
            ),
        }

    try:
        walter_db.add_stock_to_user_portfolio(stock)
        return {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps(
                {
                    "API": ADD_STOCK_API_NAME,
                    "Status": Status.SUCCESS.value,
                    "User": str(stock),
                }
            ),
        }
    except Exception as exception:
        log.error(
            "Unexpected error occurred attempting to add stock to user portfolio!",
            exception,
        )
        return {
            "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR.value,
            "body": json.dumps(
                {"API": ADD_STOCK_API_NAME, "Status": Status.FAILURE.value}
            ),
        }


def send_newsletter(event, context) -> dict:
    log.info(f"Sending newsletter to user with event: {json.dumps(event, indent=4)}")

    request = None
    try:
        request = NewsletterRequest(email=json.loads(event["body"]))
    except Exception as exception:
        log.error("Client bad request to send newsletter!", exception)
        return {
            "statusCode": HTTPStatus.BAD_REQUEST.value,
            "body": json.dumps(
                {
                    "API": SEND_NEWSLETTER_API_NAME,
                    "Status": Status.FAILURE.value,
                }
            ),
        }

    try:
        newsletters_queue.add_newsletter_request(request)
        return {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps(
                {
                    "API": SEND_NEWSLETTER_API_NAME,
                    "Status": Status.SUCCESS.value,
                    "Newsletter": request,
                }
            ),
        }
    except Exception as exception:
        log.error("Unexpected error occurred attempting to send newsletter!", exception)
        return {
            "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR.value,
            "body": json.dumps(
                {"API": SEND_NEWSLETTER_API_NAME, "Status": Status.FAILURE.value}
            ),
        }
