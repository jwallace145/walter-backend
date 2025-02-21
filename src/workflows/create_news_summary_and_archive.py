import datetime as dt
import json
from dataclasses import dataclass
from datetime import timedelta

from src.api.common.models import Status, HTTPStatus
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.config import CONFIG
from src.database.client import WalterDB
from src.database.stocks.models import Stock
from src.events.parser import WalterEventParser
from src.news.bucket import NewsSummariesBucket
from src.news.queue import NewsSummariesQueue
from src.stocks.client import WalterStocksAPI
from src.summaries.client import WalterNewsSummaryClient
from src.summaries.exceptions import GenerateNewsSummaryFailure
from src.summaries.models import NewsSummary
from src.utils.log import Logger

log = Logger(__name__).get_logger()


############
# WORKFLOW #
############


@dataclass
class CreateNewsSummaryAndArchive:
    """
    WalterWorkflow: CreateNewsSummaryAndArchive

    This workflow listens to the NewsSummariesQueue for news summary events for
    a stock and date. For each event, this workflow generates a news summary
    for the stock on the given date by getting related news articles and then
    feeding the articles into Bedrock for summarization. Because invoking Bedrock
    can be expensive, this workflow makes use of the NewsSummaryArchive and does
    not regenerate news summaries if they already exist.
    """

    WORKFLOW_NAME = "CreateNewsSummaryAndArchive"

    walter_event_parser: WalterEventParser
    walter_db: WalterDB
    walter_stocks_api: WalterStocksAPI
    walter_news_summary_client: WalterNewsSummaryClient
    news_summaries_bucket: NewsSummariesBucket
    news_summaries_queue: NewsSummariesQueue
    walter_cw: WalterCloudWatchClient

    def invoke(self, event: dict) -> dict:
        log.info(
            f"WalterWorkflow: '{CreateNewsSummaryAndArchive.WORKFLOW_NAME}' invoked!"
        )

        event = self.walter_event_parser.parse_create_news_summary_and_archive_event(
            event
        )

        symbol = event.stock
        date = event.datestamp

        archived_summary = None
        generated_summary = None
        try:
            stock = self._verify_stock_exists(symbol)
            if stock is None:
                log.warning(
                    f"Stock '{symbol}' not found in WalterDB or WalterStocksAPI!"
                )
                body = {
                    "WalterWorkflow": CreateNewsSummaryAndArchive.WORKFLOW_NAME,
                    "Status": Status.FAILURE.name,
                    "Message": "Stock not found!",
                }
                return self._get_response(HTTPStatus.OK, body)

            archived_summary = self._check_archive_for_summary(stock, date)

            if archived_summary is not None:
                log.info(f"Found news summary for stock '{stock.symbol}' in archive!")
                body = {
                    "WalterWorkflow": CreateNewsSummaryAndArchive.WORKFLOW_NAME,
                    "Status": Status.SUCCESS.name,
                    "Message": "News summary already exists!",
                    "Data": {
                        "summary": archived_summary.summary,
                    },
                }
                return self._get_response(HTTPStatus.OK, body)

            generated_summary = self._generate_news_summary(
                stock,
                date,
                CONFIG.news_summary.lookback_window_days,
                CONFIG.news_summary.number_of_articles,
                CONFIG.news_summary.context,
                CONFIG.news_summary.prompt,
                CONFIG.news_summary.max_length,
            )

            if generated_summary is None:
                body = {
                    "WalterWorkflow": CreateNewsSummaryAndArchive.WORKFLOW_NAME,
                    "Status": Status.FAILURE.name,
                    "Message": "Cannot generate news summary for stock...",
                }
                return self._get_response(HTTPStatus.OK, body)

            s3_uri = self._dump_summary_to_archive(generated_summary)

            # create success response body
            body = {
                "Workflow": CreateNewsSummaryAndArchive.WORKFLOW_NAME,
                "Status": Status.SUCCESS.value,
                "Message": "News summary created!",
                "Data": {
                    "s3_uri": s3_uri,
                    "summary": generated_summary.get_summary(),
                },
            }

            return self._get_response(HTTPStatus.CREATED, body)
        except Exception:
            log.error("Unexpected error occurred creating news summary!", exc_info=True)
            self.news_summaries_queue.delete_news_summary_request(event.receipt_handle)
            body = {
                "Workflow": CreateNewsSummaryAndArchive.WORKFLOW_NAME,
                "Status": Status.FAILURE.value,
                "Message": "Unexpected error occurred creating news summary!",
            }
            return self._get_response(HTTPStatus.INTERNAL_SERVER_ERROR, body)

    def _verify_stock_exists(self, symbol: str) -> Stock | None:
        log.info(f"Verifying stock '{symbol.upper()}' exists in WalterDB...'")
        stock = self.walter_db.get_stock(symbol)
        if stock is None:
            log.info("Stock not found in WalterDB! Checking WalterStocksAPI...")
            stock = self.walter_stocks_api.get_stock(symbol)
            if stock is None:
                log.error("Stock not found in WalterStocksAPI!")
                return None
            log.info("Stock found in WalterStocksAPI! Adding stock to WalterDB...")
            self.walter_db.add_stock(stock)
        return stock

    def _check_archive_for_summary(
        self, stock: Stock, date: dt.datetime
    ) -> NewsSummary | None:
        log.info(f"Checking for news summary in archive for stock '{stock.symbol}'...")
        summary = self.news_summaries_bucket.get_news_summary(stock, date)
        return summary

    def _generate_news_summary(
        self,
        stock: Stock,
        date: dt.datetime,
        lookback_window_days: int = CONFIG.news_summary.lookback_window_days,
        number_of_articles: int = CONFIG.news_summary.number_of_articles,
        context: str = CONFIG.news_summary.context,
        prompt: str = CONFIG.news_summary.prompt,
        max_length: int = CONFIG.news_summary.max_length,
    ) -> NewsSummary | None:
        log.info("News summary not found in archive! Generating news summary now...")
        try:
            return self.walter_news_summary_client.generate(
                stock=stock,
                start_date=date - timedelta(days=lookback_window_days),
                end_date=date,
                number_of_articles=number_of_articles,
                context=context,
                prompt=prompt,
                max_length=max_length,
            )
        except GenerateNewsSummaryFailure:
            log.error(f"Failed to generate news summary for stock '{stock.upper()}'!")
            return None

    def _dump_summary_to_archive(self, summary: NewsSummary) -> str:
        log.info(
            f"Writing news summary for stock '{summary.stock.upper()}' to archive..."
        )
        return self.news_summaries_bucket.put_news_summary(summary)

    def _get_response(self, status: HTTPStatus, body: dict) -> dict:
        return {
            "statusCode": status.value,
            "body": json.dumps(body),
        }
