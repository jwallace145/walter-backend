import json
from datetime import datetime, timedelta

import markdown

from src.clients import (
    walter_cw,
    newsletters_bucket,
    walter_stocks_api,
    walter_ses,
    newsletters_queue,
    template_engine,
    templates_bucket,
    walter_db,
    walter_ai,
    walter_event_parser,
)
from src.config import CONFIG
from src.utils.log import Logger

log = Logger(__name__).get_logger()

#############
# ARGUMENTS #
#############

TEMPLATE_NAME = "default"
END_DATE = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
START_DATE = END_DATE - timedelta(days=7)


def create_newsletter_and_send(event, context) -> dict:
    log.info(f"WalterBackend invoked! Using the following configurations:\n{CONFIG}")

    # parse event from queue
    event = walter_event_parser.parse_create_newsletter_and_send_event(event)

    try:
        # get user and portfolio info from db
        user = walter_db.get_user(event.email)
        user_stocks = walter_db.get_stocks_for_user(user)
        stocks = walter_db.get_stocks(list(user_stocks.keys()) if user_stocks else [])
        portfolio = walter_stocks_api.get_portfolio(
            user_stocks, stocks, START_DATE, END_DATE
        )

        template_spec_args = {
            "user": user.username,
            "datestamp": END_DATE,
            "portfolio_value": portfolio.get_total_equity(),
            "stocks": portfolio.get_stock_equities(),
            "news": portfolio.get_all_news(),
        }

        # get template spec with user inputs
        template_spec = template_engine.get_template_spec(
            template_name=TEMPLATE_NAME, template_spec_args=template_spec_args
        )

        # get template args from the template spec
        template_args = template_spec.get_template_args()

        # if bedrock is enabled populate the prompts with responses and add to template args
        if CONFIG.generate_responses:
            context = template_spec.get_context()
            prompt = template_spec.get_prompts().pop()
            response = walter_ai.generate_response(
                context=context, prompt=prompt.prompt, max_gen_len=prompt.max_gen_length
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

    except Exception:
        newsletters_queue.delete_newsletter_request(event.receipt_handle)
    newsletters_queue.delete_newsletter_request(event.receipt_handle)

    return {"statusCode": 200, "body": json.dumps("WalterBackend")}
