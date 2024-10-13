import json
from datetime import datetime, timedelta

from src.ai.models import Prompt
from src.clients import (
    cloudwatch,
    newsletters_bucket,
    walter_stocks_api,
    ses,
    newsletters_queue,
    template_engine,
    templates_bucket,
    walter_db,
    context_generator,
    walter_ai,
)
from src.config import CONFIG
from src.utils.events import parse_event
from src.utils.log import Logger

log = Logger(__name__).get_logger()

END_DATE = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
START_DATE = END_DATE - timedelta(days=7)


def lambda_handler(event, context) -> dict:
    log.info(f"Using the following configurations:\n{CONFIG}")

    event = parse_event(event)
    try:
        user = walter_db.get_user(event.email)
        stocks = walter_db.get_stocks_for_user(user)
        portfolio = walter_stocks_api.get_portfolio(stocks, START_DATE, END_DATE)

        template_spec = templates_bucket.get_template_spec()

        # TODO: Create utility method to convert template spec parameters to prompts
        prompts = []
        for parameter in template_spec.parameters:
            prompts.append(
                Prompt(parameter.key, parameter.prompt, parameter.max_gen_len)
            )

        responses = []
        if CONFIG.generate_responses:
            context = context_generator.get_context(user, portfolio)
            responses = walter_ai.generate_responses(context, prompts)
        else:
            log.info("Not generating responses...")

        newsletter = template_engine.render_template("default", responses)

        if CONFIG.send_newsletter:
            assets = templates_bucket.get_template_assets()
            ses.send_email(user.email, newsletter, "Walter: AI Newsletter", assets)
            newsletters_bucket.put_newsletter(user, "default", newsletter)
        else:
            log.info("Not sending newsletter...")

        if CONFIG.dump_newsletter:
            log.info("Dumping newsletter")
            open("./newsletter.html", "w").write(newsletter)
        else:
            log.info("Not dumping newsletter...")

        if CONFIG.emit_metrics:
            cloudwatch.emit_metric_number_of_emails_sent(1)
            cloudwatch.emit_metric_number_of_stocks_analyzed(len(stocks))
        else:
            log.info("Not emitting metrics")

    except Exception:
        newsletters_queue.delete_newsletter_request(event.receipt_handle)
    newsletters_queue.delete_newsletter_request(event.receipt_handle)

    return {"statusCode": 200, "body": json.dumps("WalterBackend")}
