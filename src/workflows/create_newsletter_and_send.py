import json
from datetime import datetime, timedelta

import markdown

from src.clients import (
    walter_cw,
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
)
from src.config import CONFIG
from src.utils.log import Logger

log = Logger(__name__).get_logger()

#############
# ARGUMENTS #
#############

TEMPLATE_NAME = "default"
"""(str): The name of the template to use to create the user portfolio newsletter."""

END_DATE = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
"""(str): The end date of the stock pricing data from Polygon to include in the newsletter context."""

START_DATE = END_DATE - timedelta(days=7)
"""(str): The start date of the stock pricing data from Polygon to include in the newsletter context."""

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
        # get user and portfolio info from db
        log.info("Getting user and portfolio from WalterDB...")
        user = walter_db.get_user(event.email)
        user_stocks = walter_db.get_stocks_for_user(user)
        stocks = walter_db.get_stocks(list(user_stocks.keys()) if user_stocks else [])

        summaries = []
        for stock in stocks.keys():
            summary = news_summaries_bucket.get_latest_news_summary(stock)
            summaries.append(summary)

        portfolio = walter_stocks_api.get_portfolio(
            user_stocks, stocks, START_DATE, END_DATE
        )

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
            template_name=TEMPLATE_NAME, template_spec_args=template_spec_args
        )

        # get template args from the template spec
        template_args = template_spec.get_template_args()

        # if bedrock is enabled, populate the prompts with responses and add to template args
        if CONFIG.generate_responses:
            context = template_spec.get_context()
            prompt = template_spec.get_prompts().pop()
            response = walter_ai.generate_response(
                context=context,
                prompt=prompt.prompt,
                max_output_tokens=prompt.max_gen_length,
            )
            template_args[prompt.name] = markdown.markdown(response)
        else:
            log.info("Not generating responses...")

        newsletter = template_engine.get_template(TEMPLATE_NAME, template_args)

        if CONFIG.send_newsletter:
            assets = templates_bucket.get_template_assets()
            walter_ses.send_email(user.email, newsletter, "Walter", assets)
            newsletters_bucket.put_newsletter(user, "default", newsletter)
        else:
            log.info("Not sending newsletter...")

        if CONFIG.dump_newsletter:
            log.info("Dumping newsletter")
            open("./newsletter.html", "w").write(newsletter)
        else:
            log.info("Not dumping newsletter...")

        if CONFIG.emit_metrics:
            walter_cw.emit_metric("WalterBackend.NumberOfEmailsSent", 1)
            walter_cw.emit_metric("WalterBackend.NumberOfStocksAnalyzed", len(stocks))
        else:
            log.info("Not emitting metrics")

        return {
            "statusCode": 200,
            "body": json.dumps("WalterWorkflow: CreateNewsLetterAndSend"),
        }
    except Exception:
        log.error("Unexpected error occurred creating and sending newsletter!")
        newsletters_queue.delete_newsletter_request(event.receipt_handle)
