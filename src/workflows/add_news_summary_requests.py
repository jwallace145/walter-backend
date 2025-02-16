import datetime as dt
import json
from dataclasses import dataclass
from typing import List

from src.api.common.models import HTTPStatus, Status
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.stocks.models import Stock
from src.news.queue import NewsSummaryRequest, NewsSummariesQueue
from src.utils.log import Logger

log = Logger(__name__).get_logger()

###########
# METRICS #
###########

METRICS_NUMBER_OF_STOCKS = "NumberOfStocks"
"""(str): The total number of unique stocks analyzed by WalterDB."""


############
# WORKFLOW #
############


@dataclass
class AddNewsSummaryRequests:

    walter_db: WalterDB
    news_summaries_queue: NewsSummariesQueue
    walter_cw: WalterCloudWatchClient

    def invoke(self, event: dict) -> dict:
        log.info("WalterWorkflow: AddNewsSummaryRequests invoked!")
        stocks = self._get_stocks()
        for stock in stocks:
            self._add_news_summary_request(stock)
        log.info(
            "Successfully scanned WalterDB Stocks table and submitted news summary requests for all stocks!"
        )
        self._emit_metrics(stocks)
        return self._get_response(stocks)

    def _get_stocks(self) -> List[Stock]:
        log.info(
            "Scanning WalterDB Stocks table for all stocks to generate news summaries..."
        )
        stocks = self.walter_db.get_all_stocks()
        log.info(f"Returned {len(stocks)} stocks from WalterDB Stocks table!")
        return stocks

    def _add_news_summary_request(self, stock: Stock) -> None:
        log.info(
            f"Adding news summary request for stock '{stock.symbol.upper()}' to queue"
        )
        tomorrow = dt.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + dt.timedelta(days=1)
        self.news_summaries_queue.add_news_summary_request(
            NewsSummaryRequest(
                datestamp=tomorrow,
                stock=stock.symbol.upper(),
            )
        )

    def _emit_metrics(self, stocks: List[Stock]) -> None:
        log.info("Emitting total number of stocks metric...")
        self.walter_cw.emit_metric(
            metric_name=METRICS_NUMBER_OF_STOCKS, count=len(stocks)
        )

    def _get_response(self, stocks: List[Stock]) -> dict:
        return {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps(
                {
                    "Workflow": "AddNewsSummaryRequests",
                    "Status": Status.SUCCESS.value,
                    "Message": "Added news summary requests!",
                    "Data": {
                        "news_summary_queue": self.news_summaries_queue.queue_url,
                        "number_of_stocks": len(stocks),
                    },
                }
            ),
        }
