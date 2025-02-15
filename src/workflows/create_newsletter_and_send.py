import json
from datetime import datetime, timedelta

import markdown

from src.clients import (
    newsletters_bucket,
    walter_stocks_api,
    walter_ses,
    template_engine,
    templates_bucket,
    walter_db,
    walter_ai,
    walter_event_parser,
    walter_authenticator,
    news_summaries_bucket,
    newsletters_queue,
    walter_cw,
)
from src.config import CONFIG
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


###########
# METHODS #
###########


def get_unsubscribe_link(email: str) -> str:
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
    token = walter_authenticator.generate_user_token(email)
    return "https://walterai.dev/unsubscribe?token=" + token


############
# WORKFLOW #
############


def create_newsletter_and_send_workflow(event, context) -> dict:
    log.info("WalterWorkflow: CreateNewsletterAndSend invoked!")
    log.debug(f"Using the following configurations:\n{CONFIG}")

    # parse event from queue
    event = walter_event_parser.parse_create_newsletter_and_send_event(event)

    try:
        # get user and stocks from db
        log.info("Getting user and portfolio from WalterDB...")
        user = walter_db.get_user(event.email)
        user_stocks = walter_db.get_stocks_for_user(user)
        stocks = walter_db.get_stocks(list(user_stocks.keys()) if user_stocks else [])

        # get latest stock summaries from archive
        summaries = []
        for stock in stocks.keys():
            summary = news_summaries_bucket.get_latest_news_summary(stock)
            summaries.append(summary)

        # get portfolio from db
        portfolio = walter_stocks_api.get_portfolio(
            user_stocks, stocks, START_DATE, END_DATE
        )

        # create template arguments to feed into the template spec
        template_spec_args = {
            "user": user.username,
            "datestamp": END_DATE,
            "portfolio_value": portfolio.get_total_equity(),
            "stocks": portfolio.get_stock_equities(),
            "news_summaries": summaries,
            "unsubscribe_link": get_unsubscribe_link(event.email),
        }

        # get template spec with user inputs
        template_spec = template_engine.get_template_spec(
            template_name=CONFIG.newsletter.template,
            template_spec_args=template_spec_args,
        )

        # get template args from the template spec
        template_args = template_spec.get_template_args()

        # populate the prompts with responses from llm and add to template args
        context = template_spec.get_context()
        prompt = template_spec.get_prompts().pop()
        response = walter_ai.generate_response(
            context=context,
            prompt=prompt.prompt,
            max_output_tokens=CONFIG.newsletter.max_length,
        )
        template_args[prompt.name] = markdown.markdown(response)

        # get rendered template with the llm responses to write the newsletter
        newsletter = template_engine.get_template(
            CONFIG.newsletter.template, template_args
        )

        # get referenced media assets in newsletter (default template does not use any assets but other templates do)
        assets = templates_bucket.get_template_assets()

        # send user generated newsletter
        walter_ses.send_email(user.email, newsletter, "Walter", assets)

        # dump generated newsletter to archive
        newsletters_bucket.put_newsletter(user, CONFIG.newsletter.template, newsletter)

        log.info("Emitting send newsletter success metric...")
        walter_cw.emit_metric(metric_name=METRICS_SEND_NEWSLETTER_SUCCESS, count=1)

        return {
            "statusCode": 200,
            "body": json.dumps("WalterWorkflow: CreateNewsLetterAndSend"),
        }
    except Exception:
        log.error(
            "Unexpected error occurred creating and sending newsletter!", exc_info=True
        )
        newsletters_queue.delete_newsletter_request(event.receipt_handle)
