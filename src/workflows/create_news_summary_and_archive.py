import json

from src.api.common.models import Status, HTTPStatus
from src.clients import (
    walter_event_parser,
    news_summaries_bucket,
    walter_stocks_api,
    walter_ai,
    news_summaries_queue,
)
from src.utils.log import Logger

log = Logger(__name__).get_logger()

#############
# ARGUMENTS #
#############

WORKFLOW_NAME = "CreateNewsSummaryAndArchive"
"""(str): The name of the workflow that processes events asynchronously to generate stock news summary and archive them."""

CONTEXT = "You are a financial AI advisor that summaries market news and gives readers digestible, business casual insights about the latest market movements."
"""(str): The context used to give to the LLM to generate news summaries."""

PROMPT = "Summarize the following news article about the stock '{stock}' to give a well-written concise update of the stock and any market news relating to it but write it with headers and bodies so it looks like a formatted report:\n{news}"
"""(str): The prompt used to give to the LLM to generate news summaries."""

SUMMARY_MAX_LENGTH = 2000
"""(int): The length of the news summary is controlled by the max generation length of the LLM response."""

###########
# METHODS #
###########


def get_prompt(stock: str, news: str) -> str:
    return PROMPT.format(stock=stock, news=news)


def get_response(status: HTTPStatus, body: dict) -> dict:
    return {
        "statusCode": status.value,
        "body": json.dumps(body),
    }


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
    log.info(f"WalterWorkflow: {WORKFLOW_NAME} invoked!")

    event = walter_event_parser.parse_create_news_summary_and_archive_event(event)

    try:
        log.info(f"Checking for news summary in archive for stock '{event.stock}'...")
        summary = news_summaries_bucket.get_news_summary(event.stock, event.datestamp)
        if summary is not None:
            log.info(f"Found news summary for stock '{event.stock}' in archive!")
            body = {
                "WalterWorkflow": WORKFLOW_NAME,
                "Status": Status.SUCCESS.name,
                "Message": "News summary already exists!",
            }
            return get_response(HTTPStatus.OK, body)

        log.info("News summary not found in S3!")

        log.info("Getting market news...")
        news = walter_stocks_api.get_news(event.stock, event.datestamp)

        log.info("Generating summary from news...")
        summary = walter_ai.generate_response(
            context=CONTEXT,
            prompt=get_prompt(news.stock, news.to_dict()),
            max_output_tokens=SUMMARY_MAX_LENGTH,
        )

        s3uri = news_summaries_bucket.put_news_summary(
            event.stock, summary, event.datestamp
        )

        # create response bodyp
        body = {
            "Workflow": WORKFLOW_NAME,
            "Status": Status.SUCCESS.value,
            "Message": "News summary created.",
            "Data": {
                "s3uri": s3uri,
                "model": walter_ai.get_model().get_name(),
                "articles": [url for url in news.get_article_urls()],
            },
        }

        return get_response(HTTPStatus.OK, body)
    except Exception:
        log.error("Unexpected error occurred creating news summary!")
        news_summaries_queue.delete_news_summary_request(event.receipt_handle)
