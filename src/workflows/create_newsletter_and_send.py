import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Tuple

import markdown

from src.ai.client import WalterAI
from src.api.common.models import Status, HTTPStatus
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.ses.client import WalterSESClient
from src.config import CONFIG
from src.database.client import WalterDB
from src.database.users.models import User
from src.events.parser import WalterEventParser
from src.news.bucket import NewsSummariesBucket
from src.newsletters.client import NewslettersBucket
from src.newsletters.queue import NewslettersQueue
from src.stocks.client import WalterStocksAPI
from src.stocks.models import Portfolio
from src.summaries.models import NewsSummary
from src.templates.bucket import TemplatesBucket
from src.templates.engine import TemplatesEngine
from src.templates.models import TemplateSpec, SupportedTemplate
from src.utils.log import Logger

log = Logger(__name__).get_logger()

#############
# ARGUMENTS #
#############

END_DATE = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
"""(str): The end date of the stock pricing data from Polygon to include in the newsletter context."""

START_DATE = END_DATE - timedelta(days=7)
"""(str): The start date of the stock pricing data from Polygon to include in the newsletter context."""

###########
# METRICS #
###########

METRICS_SEND_NEWSLETTER_SUCCESS = "SendNewsletterSuccess"
"""(str): The metric name for the number of successful newsletter sends."""


############
# WORKFLOW #
############


@dataclass
class CreateNewsletterAndSend:
    """
    WalterWorkflow: CreateNewsletterAndSend

    This workflow processes events from the newsletters queue to create newsletters
    and send them to the given user's email. This asynchronous workflow ensures
    that all subscribed and verified users are sent their user-specific portfolio
    emails. This workflow is invoked by listening to events in the newsletters
    queue where events are primarily created via a cron job. However, users can
    send their portfolio newsletters on-demand via the frontend as well.
    """

    WORKFLOW_NAME = "CreateNewsletterAndSend"

    walter_authenticator: WalterAuthenticator
    walter_event_parser: WalterEventParser
    walter_db: WalterDB
    walter_stocks_api: WalterStocksAPI
    walter_ai: WalterAI
    walter_ses: WalterSESClient
    walter_cw: WalterCloudWatchClient
    templates_engine: TemplatesEngine
    templates_bucket: TemplatesBucket
    news_summaries_bucket: NewsSummariesBucket
    newsletters_bucket: NewslettersBucket
    newsletters_queue: NewslettersQueue

    def invoke(self, event: dict) -> dict:
        log.info(f"WalterWorkflow: '{CreateNewsletterAndSend.WORKFLOW_NAME}' invoked!")

        event = self.walter_event_parser.parse_create_newsletter_and_send_event(event)

        try:
            user = self._get_user(event.email)

            # TODO: Send empty portfolio email if user has no stocks
            # early return if user has no stocks in their portfolio
            portfolio = self._get_portfolio(user)
            if not self._verify_portfolio_contains_stocks(portfolio):
                body = {
                    "Workflow": CreateNewsletterAndSend.WORKFLOW_NAME,
                    "Status": Status.FAILURE.value,
                    "Message": "User portfolio empty!",
                }
                return self._get_response(HTTPStatus.OK, body)

            # TODO: create another helper method in the portfolio model class?
            stocks = portfolio.get_stock_symbols()
            summaries = self._get_latest_news_summaries(stocks)
            template_spec = self._get_template_spec(
                user, portfolio, summaries, CONFIG.newsletter.template
            )
            subject, newsletter = self._get_rendered_newsletter(
                template_spec, CONFIG.newsletter.template
            )
            self._send_newsletter(user, subject, newsletter, CONFIG.newsletter.template)
            self._archive_newsletter(
                user, subject, newsletter, CONFIG.newsletter.template
            )
            self._emit_metrics()
            body = {
                "Workflow": CreateNewsletterAndSend.WORKFLOW_NAME,
                "Status": Status.SUCCESS.value,
                "Message": "Sent newsletter to user!",
            }
            return self._get_response(HTTPStatus.OK, body)
        except Exception:
            log.error(
                "Unexpected error occurred creating and sending newsletter!",
                exc_info=True,
            )
            self.newsletters_queue.delete_newsletter_request(event.receipt_handle)
            body = {
                "Workflow": CreateNewsletterAndSend.WORKFLOW_NAME,
                "Status": Status.FAILURE.value,
                "Message": "Unexpected error occurred creating and sending newsletter!",
            }
            return self._get_response(HTTPStatus.INTERNAL_SERVER_ERROR, body)

    def _get_user(self, email: str) -> User:
        log.info(f"Getting user from WalterDB with email '{email}'...")
        user = self.walter_db.get_user_by_email(email)
        return user

    def _get_portfolio(self, user: User) -> Portfolio:
        log.info("Getting user portfolio from WalterDB...")
        user_stocks = self.walter_db.get_stocks_for_user(user)
        stocks = self.walter_db.get_stocks(
            list(user_stocks.keys()) if user_stocks else []
        )
        return self.walter_stocks_api.get_portfolio(
            user_stocks, stocks, START_DATE, END_DATE
        )

    def _verify_portfolio_contains_stocks(self, portfolio: Portfolio) -> bool:
        log.info("Verifying user portfolio contains stocks...")
        if len(portfolio.get_stocks()) == 0:
            log.info("User portfolio does not contain any stocks!")
            return False
        log.info("User portfolio contains stocks!")
        return True

    def _get_latest_news_summaries(self, stocks: List[str]) -> List[NewsSummary]:
        log.info(
            f"Getting latest news summaries for {len(stocks)} stocks in user's portfolio..."
        )
        return [
            self.news_summaries_bucket.get_latest_news_summary(stock)
            for stock in stocks
        ]

    def _get_template_spec(
        self,
        user: User,
        portfolio: Portfolio,
        summaries: List[NewsSummary],
        template: SupportedTemplate = CONFIG.newsletter.template,
    ) -> TemplateSpec:
        log.info(f"Getting template spec for '{template}' template...'")
        template_spec_args = {
            "user": user.first_name,
            "datestamp": END_DATE.strftime("%Y-%m-%d"),
            "portfolio_value": f"${portfolio.get_total_equity():,.2f}",
            "stocks": [stock.to_dict() for stock in portfolio.get_stock_equities()],
            "news_summaries": summaries,
            "unsubscribe_link": self._get_unsubscribe_link(user.email),
        }

        # get template spec with user inputs
        return self.templates_engine.get_template_spec(
            template_name=template.value,
            template_spec_args=template_spec_args,
        )

    def _get_unsubscribe_link(self, email: str) -> str:
        """
        Get the unsubscribe link for the given email.

        This method creates an unsubscribe link for the given email with their authentication
        token in the returned URL. This allows WalterFrontend to use that token to make an
        authenticated Unsubscribe API request for the user associated with the given email.

        Args:
            email (str): The email of the recipient of the newsletter.

        Returns:
            (str): The authenticated unsubscribe link for the given email.
        """
        token = self.walter_authenticator.generate_user_token(email)
        return "https://walterai.dev/unsubscribe?token=" + token

    def _get_rendered_newsletter(
        self,
        template_spec: TemplateSpec,
        template: SupportedTemplate = CONFIG.newsletter.template,
    ) -> Tuple[str, str]:
        log.info(f"Rendering newsletter for user with '{template}' template...")
        # get template args from the template spec
        template_args = template_spec.get_template_args()

        # populate the prompts with responses from llm and add to template args
        context = template_spec.get_context()

        while len(template_spec.get_prompts()) > 0:
            prompt = template_spec.get_prompts().pop()
            prompt_with_context = f"Context: {context}\nPrompt: {prompt.prompt}"
            response = self.walter_ai.generate_response(
                prompt=prompt_with_context,
                max_output_tokens=prompt.max_gen_length,
            )
            # don't render the newsletter subject as markdown
            if prompt.name != "NewsletterSubject":
                response = markdown.markdown(response)
            template_args[prompt.name] = response

        subject = template_args["NewsletterSubject"].replace('"', "")
        newsletter = self.templates_engine.get_template(template.value, template_args)

        return subject, newsletter

    def _send_newsletter(
        self,
        user: User,
        subject: str,
        newsletter: str,
        template: SupportedTemplate = CONFIG.newsletter.template,
    ) -> None:
        log.info(f"Sending newsletter to user with email '{user.email}'...")
        assets = self.templates_bucket.get_template_assets(template.value)
        self.walter_ses.send_email(user.email, newsletter, subject, assets)

    def _archive_newsletter(
        self,
        user: User,
        title: str,
        newsletter: str,
        template: SupportedTemplate = CONFIG.newsletter.template,
    ) -> None:
        log.info(f"Archiving newsletter for user '{user.user_id}'...")
        self.newsletters_bucket.put_newsletter(
            user, title, template, self.walter_ai.model.model_name, newsletter
        )

    def _emit_metrics(self) -> None:
        log.info(f"Emitting '{CreateNewsletterAndSend.WORKFLOW_NAME}' metrics...")
        self.walter_cw.emit_metric(metric_name=METRICS_SEND_NEWSLETTER_SUCCESS, count=1)

    def _get_response(self, status: HTTPStatus, body: dict) -> dict:
        return {
            "statusCode": status.value,
            "body": json.dumps(body),
        }
