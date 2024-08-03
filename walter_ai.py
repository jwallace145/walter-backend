import json

from src.clients import ddb, polygon, report_generator, bedrock
from datetime import datetime, timedelta

END_DATE = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
START_DATE = END_DATE - timedelta(days=1)


def lambda_handler(event, context) -> dict:
    # get stocks from ddb and get prices from polygon
    stocks = []
    for stock in ddb.get_stocks():
        stocks.extend(polygon.get_prices(stock.symbol, START_DATE, END_DATE))

    # ingest stock data into report generator
    report_generator.ingest_stocks(stocks)

    # generate report for each user
    for user in ddb.get_users():

        # get stocks for user from ddb
        stocks = ddb.get_stocks_for_user(user)

        # generate a report for user and their stocks
        report = report_generator.generate_report(user, stocks)

        # get generative ai response from bedrock
        ai_report = bedrock.generate_response(report)

        # TODO: print ai report until emailing via ses is implemented
        print(ai_report)

    return {"statusCode": 200, "body": json.dumps("Walter AI")}
