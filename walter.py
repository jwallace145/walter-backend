import json
from datetime import datetime, timedelta

from src.ai.models import Prompt
from src.clients import (
    cloudwatch,
    newsletters_bucket,
    walter_stocks_api,
    ses,
    template_engine,
    templates_bucket,
    meta_llama3,
    walter_db,
    context_generator,
)
from src.utils.events import parse_event
from src.utils.log import Logger

log = Logger(__name__).get_logger()

END_DATE = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
START_DATE = END_DATE - timedelta(days=7)


def lambda_handler(event, context) -> dict:
    log.info("WalterAIBackend invoked!")

    event = parse_event(event)

    # get user from db
    user = walter_db.get_user(event.email)

    # get stocks for user from db
    stocks = walter_db.get_stocks_for_user(user)

    # get portfolio with latest market data and news
    portfolio = walter_stocks_api.get_portfolio(stocks, START_DATE, END_DATE)

    total_equity = portfolio.get_total_equity()
    log.info(f"'{user.email}' portfolio total equity: ${total_equity:.2f}")

    # get template spec with prompts
    template_spec = templates_bucket.get_template_spec()

    # TODO: Create utility method to convert template spec parameters to prompts
    prompts = []
    for parameter in template_spec.parameters:
        prompts.append(Prompt(parameter.key, parameter.prompt, parameter.max_gen_len))

    # get template spec responses from llm
    context = context_generator.get_context(user, portfolio)
    responses = meta_llama3.generate_responses(context, prompts)

    # render template with responses from llm
    email = template_engine.render_template("default", responses)

    # get assets for rendered template
    assets = templates_bucket.get_template_assets()

    # if the event is a dry run, skip sending email to user and dumping to S3
    if event.dry_run:
        log.info("Dry run invocation...")
        open("./newsletter.html", "w").write(email)
    else:
        ses.send_email(user.email, email, "Walter: AI Newsletter", assets)
        newsletters_bucket.put_newsletter(user, "default", email)

    cloudwatch.emit_metric_number_of_emails_sent(1)
    cloudwatch.emit_metric_number_of_stocks_analyzed(len(stocks))

    return {"statusCode": 200, "body": json.dumps("WalterAIBackend")}
