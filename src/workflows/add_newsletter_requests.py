import json
from typing import List

from src.clients import walter_db, newsletters_queue, walter_cw
from src.database.users.models import User
from src.newsletters.queue import NewsletterRequest

from src.utils.log import Logger

log = Logger(__name__).get_logger()

###########
# METRICS #
###########

METRICS_NUMBER_OF_USERS = "NumberOfUsers"
"""(str): The total number of Walter users (all users count, even unsubscribed/unverified users)."""

METRICS_NUMBER_OF_VERIFIED_USERS = "NumberOfVerifiedUsers"
"""(str): The total number of verified Walter users."""

METRICS_NUMBER_OF_UNVERIFIED_USERS = "NumberOfUnverifiedUsers"
"""(str): The total number of unverified Walter users."""

METRICS_NUMBER_OF_SUBSCRIBED_USERS = "NumberOfSubscribedUsers"
"""(str): The total number of subscribed Walter users."""

METRICS_NUMBER_OF_UNSUBSCRIBED_USERS = "NumberOfUnsubscribedUsers"
"""(str): The total number of unsubscribed Walter users."""


def emit_metrics(users: List[User]) -> None:
    log.info("Emitting metrics about the total number of users...")
    verified_users = [user for user in users if user.verified]
    unverified_users = [user for user in users if not user.verified]
    subscribed_users = [user for user in users if user.subscribed]
    unsubscribed_users = [user for user in users if not user.subscribed]
    walter_cw.emit_metric(metric_name=METRICS_NUMBER_OF_USERS, count=len(users))
    walter_cw.emit_metric(
        metric_name=METRICS_NUMBER_OF_VERIFIED_USERS, count=len(verified_users)
    )
    walter_cw.emit_metric(
        metric_name=METRICS_NUMBER_OF_UNVERIFIED_USERS, count=len(unverified_users)
    )
    walter_cw.emit_metric(
        metric_name=METRICS_NUMBER_OF_SUBSCRIBED_USERS, count=len(subscribed_users)
    )
    walter_cw.emit_metric(
        metric_name=METRICS_NUMBER_OF_UNSUBSCRIBED_USERS, count=len(unsubscribed_users)
    )


############
# WORKFLOW #
############


def add_newsletter_requests_workflow(event, context) -> dict:
    """
    Get users from WalterDB and send newsletters to all verified and subscribed users.
    """
    log.info("WalterWorkflow: AddNewsletterRequests invoked!")

    # get all users from db
    log.info("Scanning WalterDB Users table for all users...")
    users = walter_db.get_users()
    log.info(f"WalterDB returned {len(users)} users!")

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

    # emit metrics about the total number of users
    emit_metrics(users)

    return {
        "statusCode": 200,
        "body": json.dumps("WalterWorkflow: AddNewsletterRequests"),
    }
