import datetime as dt
import json
from dataclasses import dataclass
from datetime import timedelta

from src.api.common.models import Status, HTTPStatus
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.config import CONFIG
from src.events.parser import WalterEventParser
from src.news.bucket import NewsSummariesBucket
from src.news.queue import NewsSummariesQueue
from src.summaries.client import WalterNewsSummaryClient
from src.summaries.models import NewsSummary
from src.utils.log import Logger

log = Logger(__name__).get_logger()

###########
# METRICS #
###########

METRICS_NUMBER_OF_ARTICLES_PARSED = "NumberOfArticlesParsed"
"""(str): The total number of articles parsed by Walter to create a news summary."""


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
        try:
            summary = self._check_archive_for_summary(event.stock, event.datestamp)
            if summary is not None:
                log.info(
                    f"Found news summary for stock '{event.stock.upper()}' in archive!"
                )
                body = {
                    "WalterWorkflow": CreateNewsSummaryAndArchive.WORKFLOW_NAME,
                    "Status": Status.SUCCESS.name,
                    "Message": "News summary already exists!",
                }
                return self._get_response(HTTPStatus.OK, body)

            summary = self._generate_news_summary(
                event.stock,
                event.datestamp,
                CONFIG.news_summary.lookback_window_days,
                CONFIG.news_summary.number_of_articles,
            )

            s3_uri = self._dump_summary_to_archive(summary)

            self._emit_metrics(summary)

            # create success response body
            body = {
                "Workflow": CreateNewsSummaryAndArchive.WORKFLOW_NAME,
                "Status": Status.SUCCESS.value,
                "Message": "News summary created!",
                "Data": {
                    "s3_uri": s3_uri,
                    "summary": summary.get_summary(),
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

    def _check_archive_for_summary(self, stock: str, date: dt.datetime) -> str:
        log.info(f"Checking for news summary in archive for stock '{stock.upper()}'...")
        summary = self.news_summaries_bucket.get_news_summary(stock, date)
        return summary

    def _generate_news_summary(
        self,
        stock: str,
        date: dt.datetime,
        lookback_window_days: int = CONFIG.news_summary.lookback_window_days,
        number_of_articles: int = CONFIG.news_summary.number_of_articles,
    ) -> NewsSummary:
        log.info("News summary not found in archive! Generating news summary now...")
        return self.walter_news_summary_client.generate(
            stock=stock,
            start_date=date - timedelta(days=lookback_window_days),
            end_date=date,
            number_of_articles=number_of_articles,
        )

    def _dump_summary_to_archive(self, summary: NewsSummary) -> str:
        log.info(
            f"Writing news summary for stock '{summary.stock.upper()}' to archive..."
        )
        return self.news_summaries_bucket.put_news_summary(summary)

    def _emit_metrics(self, summary: NewsSummary) -> None:
        log.info("Emitting total number of articles parsed metric...")
        self.walter_cw.emit_metric(
            metric_name=METRICS_NUMBER_OF_ARTICLES_PARSED,
            count=len(summary.news.articles),
        )

    def _get_response(self, status: HTTPStatus, body: dict) -> dict:
        return {
            "statusCode": status.value,
            "body": json.dumps(body),
        }
