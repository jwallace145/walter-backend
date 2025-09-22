import pytest

from src.factory import ClientFactory
from src.workflows.common.router import WorkflowRouter, Workflows

task = {
    "Records": [
        {
            "messageId": "test-message-id",
            "receiptHandle": "test-receipt-handle",
            "body": '{"workflow_name": "SyncUserTransactions", "user_id": "user-001", "account_id": "acct-001"}',
            "attributes": {
                "ApproximateReceiveCount": "1",
                "AWSTraceHeader": "test-aws-trace-header",
                "SentTimestamp": "test-sent-timestamp",
                "SenderId": "test-sender-id",
                "ApproximateFirstReceiveTimestamp": "test-approximate-first-receive-timestamp",
            },
            "md5OfMessageAttributes": "test-md5-of-message-attributes",
            "md5OfBody": "test-md5-of-body",
            "eventSource": "aws:sqs",
            "eventSourceARN": "arn:aws:sqs:us-east-1:000000000000:WalterBackend-SyncTransactions-Queue-dev",
            "awsRegion": "us-east-1",
        }
    ]
}


@pytest.fixture
def workflow_router(
    client_factory: ClientFactory,
) -> WorkflowRouter:
    return WorkflowRouter(
        client_factory=client_factory,
    )


def test_get_workflow_from_string() -> None:
    assert (
        Workflows.from_string("UpdateSecurityPrices")
        == Workflows.UPDATE_SECURITY_PRICES
    )
    assert (
        Workflows.from_string("SyncUserTransactions")
        == Workflows.SYNC_USER_TRANSACTIONS
    )


def test_get_workflow_name_from_task(
    workflow_router: WorkflowRouter,
) -> None:
    assert workflow_router._get_workflow_details(task) == (
        "SyncUserTransactions",
        "test-message-id",
    )
