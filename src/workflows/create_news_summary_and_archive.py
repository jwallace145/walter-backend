import json

from src.api.common.models import Status
from src.clients import (
    walter_event_parser,
    news_summaries_bucket,
    walter_stocks_api,
    walter_ai,
)
from src.utils.log import Logger

log = Logger(__name__).get_logger()

#############
# ARGUMENTS #
#############

SUMMARY_MAX_LENGTH = 1000
"""(int): The length of the news summary is controlled by the max generation length of the LLM response."""

############
# WORKFLOW #
############


def create_news_summary_and_archive_workflow(event, context) -> dict:
    log.info("WalterWorkflow: CreateNewsSummaryAndArchive invoked!")

    event = walter_event_parser.parse_create_news_summary_and_archive_event(event)

    log.info("Checking S3 for news summary...")
    summary = news_summaries_bucket.get_news_summary(event.stock)
    if summary is not None:
        log.info("Found news summary in S3!")
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "WalterWorkflow": "CreateNewsSummaryAndArchive",
                    "Status": Status.SUCCESS.name,
                    "Message": "News summary already exists!",
                }
            ),
        }
    log.info("News summary not found in S3!")

    log.info("Getting recent market news from AlphaVantage...")
    news = walter_stocks_api.get_news(event.stock)

    log.info("Generating summary from news...")
    summary = walter_ai.generate_response(
        context="You are a financial AI advisor that summaries market news and gives readers digestible, business casual insights about the latest market movements.",
        prompt=f"Summarize the following news article about the stock '{news.symbol}':\n{news.news}",
        max_gen_len=SUMMARY_MAX_LENGTH,
    )

    news_summaries_bucket.put_news_summary(event.stock, summary)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "WalterWorkflow": "CreateNewsSummaryAndArchive",
                "Status": Status.SUCCESS.name,
                "Message": "News summary created!",
            }
        ),
    }
