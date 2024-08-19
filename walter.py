import json
from datetime import datetime, timedelta

from src.clients import (
    bedrock,
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
)

END_DATE = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
START_DATE = END_DATE - timedelta(days=7)


def lambda_handler(event, context) -> dict:
    # get all stocks from ddb
    stocks = stocks_table.list_stocks()

    # get prices for each stock from polygon
    prices = []
    for stock in stocks:
        prices.extend(polygon.get_prices(stock.symbol, START_DATE, END_DATE))

    # ingest stock data into report generator
    report_generator.ingest_stocks(prices)

    # get all users in ddb
    users = users_table.get_users()

    # generate a newsletter for each user
    for user in users:

        # get stocks for user from ddb
        stocks = users_stocks_table.get_stocks_for_user(user)

        # get prompts from template spec
        template_spec = templates_bucket.get_template_spec()

        # get generative ai response from bedrock for eaach prompt for template
        responses = bedrock.generate_responses(template_spec.parameters)

        # render template with ai responses
        email = template_engine.render_template(user, "default", responses)

        # get images to send with email
        assets = templates_bucket.get_template_assets()

        # send email to user
        ses.send_email(user.email, email, "Walter: AI Newsletter", assets)

        newsletters_bucket.put_newsletter(user, "default", email)

    # emit metrics
    cloudwatch.emit_metric_number_of_emails_sent(len(users))
    cloudwatch.emit_metric_number_of_stocks_analyzed(len(stocks))
    cloudwatch.emit_metric_number_of_subscribed_users(len(users))

    return {"statusCode": 200, "body": json.dumps("WalterAIBackend")}
