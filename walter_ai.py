import json
from datetime import datetime, timedelta

from src.clients import bedrock, cloudwatch, ddb, polygon, report_generator

END_DATE = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
START_DATE = END_DATE - timedelta(days=1)


def lambda_handler(event, context) -> dict:
    # get stocks from ddb and get prices from polygon
    prices = []
    stocks = ddb.get_stocks()
    for stock in stocks:
        prices.extend(polygon.get_prices(stock.symbol, START_DATE, END_DATE))

    # ingest stock data into report generator
    report_generator.ingest_stocks(prices)

    # generate report for each user
    users = ddb.get_users()
    for user in users:

        # get stocks for user from ddb
        stocks = ddb.get_stocks_for_user(user)

        # generate a report for user and their stocks
        report = report_generator.generate_report(user, stocks)

        # get generative ai response from bedrock
        ai_report = bedrock.generate_response(report)

        # TODO: print ai report until emailing via ses is implemented
        print(ai_report)

    # emit metrics
    cloudwatch.emit_metric_number_of_emails_sent(len(users))
    cloudwatch.emit_metric_number_of_stocks_analyzed(len(stocks))
    cloudwatch.emit_metric_number_of_subscribed_users(len(users))

    return {"statusCode": 200, "body": json.dumps("Walter AI")}
