import json
from datetime import datetime, timedelta

from src.clients import (
    walter_cw,
    newsletters_bucket,
    walter_stocks_api,
    ses,
    newsletters_queue,
    template_engine,
    template_engine_refactor,
    templates_bucket,
    walter_db,
    walter_ai,
)
from src.config import CONFIG
from src.utils.events import parse_event
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
    event = parse_event(event)

    try:
        # get user and portfolio info from db
        user = walter_db.get_user(event.email)
        user_stocks = walter_db.get_stocks_for_user(user)
        stocks = walter_db.get_stocks(list(user_stocks.keys()) if user_stocks else [])
        portfolio = walter_stocks_api.get_portfolio(
            user_stocks, stocks, START_DATE, END_DATE
        )

        # get template spec with user inputs
        template_spec = template_engine_refactor.get_template_spec(
            template_name=TEMPLATE_NAME,
            user=user.username,
            datestamp=END_DATE,
            portfolio_value=portfolio.get_total_equity(),
            stocks=portfolio.get_stock_equities(),
        )

        template_args = template_spec.get_template_args()
        if CONFIG.generate_responses:
            context = template_spec.get_context()
            prompt = template_spec.get_prompts().pop()
            template_args[prompt.name] = walter_ai.generate_response(
                context=context, prompt=prompt.prompt, max_gen_len=prompt.max_gen_length
            )
        else:
            log.info("Not generating responses...")

        newsletter = template_engine.render_template(TEMPLATE_NAME, template_args)

        if CONFIG.send_newsletter:
            assets = templates_bucket.get_template_assets()
            ses.send_email(user.email, newsletter, "Walter", assets)
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
