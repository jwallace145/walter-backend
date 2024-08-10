import json
from datetime import datetime, timedelta

from src.clients import (
    bedrock,
    cloudwatch,
    ddb,
    polygon,
    report_generator,
    template_engine,
    ses,
)

END_DATE = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
START_DATE = END_DATE - timedelta(days=7)


def lambda_handler(event, context) -> dict:
    # get all stocks from ddb
    stocks = ddb.get_stocks()

    # get prices for each stock from polygon
    prices = []
    for stock in stocks:
        prices.extend(polygon.get_prices(stock.symbol, START_DATE, END_DATE))

    # ingest stock data into report generator
    report_generator.ingest_stocks(prices)

    # get all users in ddb
    users = ddb.get_users()

    # generate a newsletter for each user
    for user in users:

        # get stocks for user from ddb
        stocks = ddb.get_stocks_for_user(user)

        # get prompts from template spec
        parameters = template_engine.get_template_spec()

        # get generative ai response from bedrock for eaach prompt for template
        responses = bedrock.generate_responses(parameters)

        # render template with ai responses
        email = template_engine.render_template("default", responses)

        # get images to send with email
        images = template_engine.get_template_images()

        # send email to user
        ses.send_email(user.email, email, "Walter: AI Newsletter", images)

    # emit metrics
    cloudwatch.emit_metric_number_of_emails_sent(len(users))
    cloudwatch.emit_metric_number_of_stocks_analyzed(len(stocks))
    cloudwatch.emit_metric_number_of_subscribed_users(len(users))

    return {"statusCode": 200, "body": json.dumps("WalterAIBackend")}
