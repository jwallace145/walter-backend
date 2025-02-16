import json
from dataclasses import dataclass
from typing import List

from src.api.common.models import HTTPStatus, Status
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.users.models import User
from src.newsletters.queue import NewsletterRequest, NewslettersQueue
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


############
# WORKFLOW #
############


@dataclass
class AddNewsletterRequests:
    """
    WalterWorkflow: AddNewsletterRequests

    This workflow scans WalterDB for all users and submits newsletter requests
    to the queue for each subscribed and verified user. The CreateNewsletterAndSend
    workflow asynchronously processes the newsletter requests to send Walter's
    user-specific newsletter to each user. This workflow is invoked on a cron schedule
    and ensures that Walter is sending newsletters on the specified schedule.
    """

    WORKFLOW_NAME = "AddNewsletterRequests"

    walter_db: WalterDB
    newsletters_queue: NewslettersQueue
    walter_cw: WalterCloudWatchClient

    def invoke(self, event: dict) -> dict:
        log.info(f"WalterWorkflow: '{AddNewsletterRequests.WORKFLOW_NAME}' invoked!")
        users = self._get_users()
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

            self._add_newsletter_request(user)

        self._emit_metrics(users)

        return self._get_response(users)

    def _get_users(self) -> List[User]:
        log.info("Scanning WalterDB Users table for all users...")
        users = self.walter_db.get_users()
        log.info(f"WalterDB returned {len(users)} users!")
        return users

    def _add_newsletter_request(self, user: User) -> None:
        log.info(f"Adding newsletter request to the queue for user: '{user.email}'")
        request = NewsletterRequest(email=user.email)
        self.newsletters_queue.add_newsletter_request(request)

    def _emit_metrics(self, users: List[User]) -> None:
        log.info("Emitting metrics about the total number of users...")
        verified_users = [user for user in users if user.verified]
        unverified_users = [user for user in users if not user.verified]
        subscribed_users = [user for user in users if user.subscribed]
        unsubscribed_users = [user for user in users if not user.subscribed]
        self.walter_cw.emit_metric(
            metric_name=METRICS_NUMBER_OF_USERS, count=len(users)
        )
        self.walter_cw.emit_metric(
            metric_name=METRICS_NUMBER_OF_VERIFIED_USERS, count=len(verified_users)
        )
        self.walter_cw.emit_metric(
            metric_name=METRICS_NUMBER_OF_UNVERIFIED_USERS, count=len(unverified_users)
        )
        self.walter_cw.emit_metric(
            metric_name=METRICS_NUMBER_OF_SUBSCRIBED_USERS, count=len(subscribed_users)
        )
        self.walter_cw.emit_metric(
            metric_name=METRICS_NUMBER_OF_UNSUBSCRIBED_USERS,
            count=len(unsubscribed_users),
        )

    def _get_response(self, users: List[User]) -> dict:
        return {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps(
                {
                    "Workflow": AddNewsletterRequests.WORKFLOW_NAME,
                    "Status": Status.SUCCESS.value,
                    "Message": "Added newsletter requests!",
                    "Data": {
                        "newsletters_queue": self.newsletters_queue.queue_url,
                        "number_of_users": len(users),
                    },
                }
            ),
        }
