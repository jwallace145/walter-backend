import datetime as dt
import json

from src.clients import walter_db, news_summaries_queue
from src.news.queue import NewsSummaryRequest
from src.utils.log import Logger

log = Logger(__name__).get_logger()


def add_news_summary_requests_workflow(event, context) -> dict:
    log.info("WalterWorkflow: AddNewsSummaryRequests invoked!")

    log.info(
        "Scanning WalterDB Stocks table for all stocks to generate news summaries..."
    )
    for stock in walter_db.get_all_stocks():
        log.info(
            f"Add news summary request for stock '{stock.symbol.upper()}' to queue"
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
    return {
        "statusCode": 200,
        "body": json.dumps("WalterWorkflow: AddNewsSummaryRequests"),
    }
