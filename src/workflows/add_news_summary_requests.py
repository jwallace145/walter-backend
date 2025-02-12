import datetime as dt
import json
from typing import List

from src.clients import walter_db, news_summaries_queue, walter_cw
from src.database.stocks.models import Stock
from src.news.queue import NewsSummaryRequest
from src.utils.log import Logger

log = Logger(__name__).get_logger()

###########
# METRICS #
###########

METRICS_NUMBER_OF_STOCKS = "NumberOfStocks"
"""(str): The total number of unique stocks analyzed by WalterDB."""


def emit_metrics(stocks: List[Stock]) -> None:
    log.info("Emitting total number of stocks metric...")
    walter_cw.emit_metric(metric_name=METRICS_NUMBER_OF_STOCKS, count=len(stocks))


############
# WORKFLOW #
############


def add_news_summary_requests_workflow(event, context) -> dict:
    log.info("WalterWorkflow: AddNewsSummaryRequests invoked!")

    log.info(
        "Scanning WalterDB Stocks table for all stocks to generate news summaries..."
    )
    stocks = walter_db.get_all_stocks()
    log.info(f"Returned {len(stocks)} stocks from WalterDB Stocks table!")

    # add news summary request to queue for each stock for the next day
    for stock in stocks:
        log.info(
            f"Adding news summary request for stock '{stock.symbol.upper()}' to queue"
        )
        news_summaries_queue.add_news_summary_request(
            NewsSummaryRequest(
                datestamp=dt.datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                + dt.timedelta(days=1),
                stock=stock.symbol.upper(),
            )
        )

    log.info(
        "Successfully scanned WalterDB Stocks table and submitted news summary requests for all stocks!"
    )

    # emit metrics about the total number of stocks in db
    emit_metrics(stocks)

    return {
        "statusCode": 200,
        "body": json.dumps("WalterWorkflow: AddNewsSummaryRequests"),
    }
