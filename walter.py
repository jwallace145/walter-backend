import json
from datetime import datetime, timedelta

from src.ai.models import Prompt
from src.clients import (
    cloudwatch,
    newsletters_bucket,
    polygon,
    report_generator,
    ses,
    template_engine,
    templates_bucket,
    stocks_table,
    users_table,
    users_stocks_table,
    meta_llama3,
)
from src.utils.log import Logger

log = Logger(__name__).get_logger()

END_DATE = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
START_DATE = END_DATE - timedelta(days=7)


def lambda_handler(event, context) -> dict:
    log.info("WalterAIBackend invoked!")
    stocks = stocks_table.list_stocks()

    prices = []
    for stock in stocks:
        prices.extend(polygon.get_prices(stock.symbol, START_DATE, END_DATE))

    report_generator.ingest_stocks(prices)

    users = users_table.get_users()
    for user in users:
        stocks = users_stocks_table.get_stocks_for_user(user)
        template_spec = templates_bucket.get_template_spec()

        # TODO: Create utility method to convert template spec parameters to prompts
        prompts = []
        for parameter in template_spec.parameters:
            prompts.append(
                Prompt(parameter.key, parameter.prompt, parameter.max_gen_len)
            )

        responses = meta_llama3.generate_responses(prompts)
        email = template_engine.render_template("default", responses)
        assets = templates_bucket.get_template_assets()

        # if the event is a dry run, skip sending email to user and dumping to S3
        dry_run = event["dry_run"]
        if dry_run:
            log.info("Dry run invocation...")
            open("./newsletter.html", "w").write(email)
        else:
            ses.send_email(user.email, email, "Walter: AI Newsletter", assets)
            newsletters_bucket.put_newsletter(user, "default", email)

    cloudwatch.emit_metric_number_of_emails_sent(len(users))
    cloudwatch.emit_metric_number_of_stocks_analyzed(len(stocks))
    cloudwatch.emit_metric_number_of_subscribed_users(len(users))

    return {"statusCode": 200, "body": json.dumps("WalterAIBackend")}
