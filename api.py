from src.api.add_stock import AddStock
from src.api.create_user import CreateUser
from src.api.send_newsletter import SendNewsletter
from src.utils.log import Logger

log = Logger(__name__).get_logger()

############
# HANDLERS #
############


def create_user(event, context) -> dict:
    return CreateUser(event).invoke()


def add_stock(event, context) -> dict:
    return AddStock(event).invoke()


def send_newsletter(event, context) -> dict:
    return SendNewsletter(event).invoke()
