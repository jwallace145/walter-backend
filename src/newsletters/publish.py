import json

from src.clients import walter_db, newsletters_queue
from src.newsletters.queue import NewsletterRequest

from src.utils.log import Logger

log = Logger(__name__).get_logger()


def add_newsletter_to_queue(event, context) -> dict:
    """
    Get users from WalterDB and send newsletters to all verified and subscribed users.
    """
    log.info("WalterNewsletters invoked!")

    # get all users from db
    users = walter_db.get_users()

    for user in users:

        # ensure user email address is verified
        if not user.verified:
            log.info(
                f"Not sending newsletter to '{user.email}' as email address has not been verified."
            )
            continue

        # ensure user is currently subscribed to newsletter
        if not user.subscribed:
            log.info(
                f"Not sending newsletter to '{user.email}' because user is not currently subscribed."
            )
            continue

        log.info(f"Adding newsletter request to the queue for user: '{user.email}'")
        request = NewsletterRequest(email=user.email)
        newsletters_queue.add_newsletter_request(request)

    return {"statusCode": 200, "body": json.dumps("WalterNewsletters")}
