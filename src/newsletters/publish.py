import json

from src.clients import walter_db, newsletters_queue
from src.newsletters.queue import NewsletterRequest

from src.utils.log import Logger

log = Logger(__name__).get_logger()


def add_newsletter_to_queue(event, context) -> dict:
    log.info("WalterNewsletters invoked!")

    users = walter_db.get_users()
    for user in users:
        log.info(f"Adding newsletter request to the queue for user: '{user.email}'")
        request = NewsletterRequest(email=user.email)
        newsletters_queue.add_newsletter_request(request)

    return {"statusCode": 200, "body": json.dumps("WalterNewsletters")}
