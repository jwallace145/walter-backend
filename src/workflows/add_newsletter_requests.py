import json
from dataclasses import dataclass
from typing import List
import datetime

from src.api.common.models import HTTPStatus, Status
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.users.models import User
from src.newsletters.queue import NewsletterRequest, NewslettersQueue
from src.utils.log import Logger

log = Logger(__name__).get_logger()

#############
# CONSTANTS #
#############

NOW = datetime.datetime.now(datetime.UTC)
"""(datetime): The current timestamp in UTC."""

###########
# METRICS #
###########


@dataclass(frozen=True)
class AddNewsletterRequestsMetrics:
    """Metrics emitted by AddNewsletterRequests workflow."""

    # metric names
    NUMBER_OF_USERS = "NumberOfUsers"
    NUMBER_OF_VERIFIED_USERS = "NumberOfVerifiedUsers"
    NUMBER_OF_UNVERIFIED_USERS = "NumberOfUnverifiedUsers"
    NUMBER_OF_SUBSCRIBED_USERS = "NumberOfSubscribedUsers"
    NUMBER_OF_UNSUBSCRIBED_USERS = "NumberOfUnsubscribedUsers"
    NUMBER_OF_PAID_USERS = "NumberOfPaidUsers"
    NUMBER_OF_FREE_TRIAL_USERS = "NumberOfFreeTrialUsers"
    NUMBER_OF_EXPIRED_FREE_TRIAL_USERS = "NumberOfExpiredFreeTrialUsers"
    NUMBER_OF_NEWSLETTERS_SENT = "NumberOfNewslettersSent"

    # fields
    number_of_users: int
    number_of_verified_users: int
    number_of_unverified_users: int
    number_of_subscribed_users: int
    number_of_unsubscribed_users: int
    number_of_paid_users: int
    number_of_free_trial_users: int
    number_of_expired_free_trial_users: int
    number_newsletters_sent: int = 0


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
        users = self._get_all_users()

        # iterate over all users in db
        num_newsletters_sent: int = 0
        for user in users:

            # ensure user is verified
            if not user.verified:
                log.info(
                    f"Not sending newsletter to '{user.email}' as email address has not been verified."
                )
                continue

            # ensure the user is subscribed
            if not user.subscribed:
                log.info(
                    f"Not sending newsletter to '{user.email}' because user is unsubscribed.."
                )
                continue

            # ensure user has active Stripe newsletter subscription or is in free trial
            if (
                user.stripe_subscription_id is None
                and NOW > user.free_trial_end_date.astimezone(datetime.UTC)
            ):
                log.info(
                    f"Not sending newsletter to '{user.email}' because user has no active Stripe newsletter subscription and their free trial expired on '{user.free_trial_end_date}'."
                )
                continue

            # send newsletter to user
            num_newsletters_sent += 1
            self._add_newsletter_request(user)

        metrics = self._emit_metrics(users, num_newsletters_sent)

        return self._get_response(metrics)

    def _get_all_users(self) -> List[User]:
        log.info("Scanning WalterDB Users table for all users...")
        users = self.walter_db.get_users()
        log.info(f"WalterDB returned {len(users)} users!")
        return users

    def _add_newsletter_request(self, user: User) -> None:
        log.info(f"Adding newsletter request to the queue for user: '{user.email}'")
        request = NewsletterRequest(email=user.email)
        self.newsletters_queue.add_newsletter_request(request)

    def _emit_metrics(
        self, users: List[User], num_newsletters_sent: int
    ) -> AddNewsletterRequestsMetrics:
        log.info("Emitting metrics about the total number of users...")
        verified_users = [user for user in users if user.verified]
        unverified_users = [user for user in users if not user.verified]
        subscribed_users = [user for user in users if user.subscribed]
        unsubscribed_users = [user for user in users if not user.subscribed]
        paid_users = [user for user in users if user.stripe_subscription_id]
        free_trial_users = [
            user
            for user in users
            if not user.stripe_subscription_id
            and NOW <= user.free_trial_end_date.astimezone(datetime.UTC)
        ]
        expired_free_trial_users = [
            user
            for user in users
            if not user.stripe_subscription_id
            and NOW > user.free_trial_end_date.astimezone(datetime.UTC)
        ]
        metrics = AddNewsletterRequestsMetrics(
            number_of_users=len(users),
            number_of_verified_users=len(verified_users),
            number_of_unverified_users=len(unverified_users),
            number_of_subscribed_users=len(subscribed_users),
            number_of_unsubscribed_users=len(unsubscribed_users),
            number_of_paid_users=len(paid_users),
            number_of_free_trial_users=len(free_trial_users),
            number_of_expired_free_trial_users=len(expired_free_trial_users),
            number_newsletters_sent=num_newsletters_sent,
        )
        self.walter_cw.emit_metric(
            metric_name=AddNewsletterRequestsMetrics.NUMBER_OF_USERS,
            count=metrics.number_of_users,
        )
        self.walter_cw.emit_metric(
            metric_name=AddNewsletterRequestsMetrics.NUMBER_OF_VERIFIED_USERS,
            count=metrics.number_of_verified_users,
        )
        self.walter_cw.emit_metric(
            metric_name=AddNewsletterRequestsMetrics.NUMBER_OF_UNVERIFIED_USERS,
            count=metrics.number_of_unverified_users,
        )
        self.walter_cw.emit_metric(
            metric_name=AddNewsletterRequestsMetrics.NUMBER_OF_SUBSCRIBED_USERS,
            count=metrics.number_of_subscribed_users,
        )
        self.walter_cw.emit_metric(
            metric_name=AddNewsletterRequestsMetrics.NUMBER_OF_UNSUBSCRIBED_USERS,
            count=metrics.number_of_unsubscribed_users,
        )
        self.walter_cw.emit_metric(
            metric_name=AddNewsletterRequestsMetrics.NUMBER_OF_PAID_USERS,
            count=metrics.number_of_paid_users,
        )
        self.walter_cw.emit_metric(
            metric_name=AddNewsletterRequestsMetrics.NUMBER_OF_FREE_TRIAL_USERS,
            count=metrics.number_of_free_trial_users,
        )
        self.walter_cw.emit_metric(
            metric_name=AddNewsletterRequestsMetrics.NUMBER_OF_EXPIRED_FREE_TRIAL_USERS,
            count=metrics.number_of_expired_free_trial_users,
        )
        self.walter_cw.emit_metric(
            metric_name=AddNewsletterRequestsMetrics.NUMBER_OF_NEWSLETTERS_SENT,
            count=metrics.number_newsletters_sent,
        )
        return metrics

    def _get_response(
        self,
        metrics: AddNewsletterRequestsMetrics,
    ) -> dict:
        return {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps(
                {
                    "Workflow": AddNewsletterRequests.WORKFLOW_NAME,
                    "Status": Status.SUCCESS.value,
                    "Message": "Added newsletter requests!",
                    "Data": {
                        "newsletters_queue": self.newsletters_queue.queue_url,
                        "total_number_of_users_count": metrics.number_of_users,
                        "verified_users_count": metrics.number_of_verified_users,
                        "unverified_users_count": metrics.number_of_unverified_users,
                        "subscribed_users_count": metrics.number_of_subscribed_users,
                        "unsubscribed_users_count": metrics.number_of_unsubscribed_users,
                        "paid_users_count": metrics.number_of_paid_users,
                        "free_trial_users_count": metrics.number_of_free_trial_users,
                        "expired_free_trial_users_count": metrics.number_of_expired_free_trial_users,
                        "total_number_of_newsletter_sent": metrics.number_newsletters_sent,
                    },
                }
            ),
        }
