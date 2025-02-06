import json

from src.api.common.models import Status, HTTPStatus
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
    """
    Create a summary of the latest market news for the given stock and archive in S3.

    The purpose of this workflow is to create news summaries of various stocks and dump them
    to S3 daily. To generate the news summaries, this method makes API calls to Bedrock to
    invoke foundational models and get LLM responses that summarize the given articles. The
    calls to Bedrock are expensive with respect to both latency and money. So, this method
    caches the stock news summaries in S3 and does not recompute them if it detects that
    there is already a daily summary.
    """
    log.info("WalterWorkflow: CreateNewsSummaryAndArchive invoked!")

    event = walter_event_parser.parse_create_news_summary_and_archive_event(event)

    log.info("Checking S3 for news summary...")
    summary = news_summaries_bucket.get_news_summary(event.stock, event.datestamp)
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
    news = walter_stocks_api.get_news(event.stock, event.datestamp)

    log.info("Generating summary from news...")
    summary = walter_ai.generate_response(
        context="You are a financial AI advisor that summaries market news and gives readers digestible, business casual insights about the latest market movements.",
        prompt=f"Summarize the following news article about the stock '{news.stock}' to give a well-written concise update of the stock and any market news relating to it but write it with headers and bodies so it looks like a formatted report:\n{news.to_dict()}",
        max_gen_len=SUMMARY_MAX_LENGTH,
    )

    s3uri = news_summaries_bucket.put_news_summary(event.stock, summary)

    # create response body
    body = {
        "Workflow": "CreateNewsSummaryAndArchive",
        "Status": Status.SUCCESS.value,
        "Message": "News summary created.",
        "Data": {
            "s3uri": s3uri,
            "model": walter_ai.get_model().get_name(),
            "articles": [url for url in news.get_article_urls()],
        },
    }

    # return successful response
    return {
        "statusCode": HTTPStatus.OK.value,
        "body": json.dumps(body),
    }
