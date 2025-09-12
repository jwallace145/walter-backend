import json
from typing import List

import pytest

from src.database.accounts.models import Account
from src.database.client import WalterDB
from src.environment import Domain
from src.metrics.client import DatadogMetricsClient
from src.workflows.common.models import WorkflowResponse, WorkflowStatus
from src.workflows.sync_user_transactions import SyncUserTransactions
from tst.plaid.mock import MockPlaidClient


@pytest.fixture
def sync_user_transactions_workflow(
    plaid_client: MockPlaidClient,
    walter_db: WalterDB,
    datadog_metrics: DatadogMetricsClient,
) -> SyncUserTransactions:
    return SyncUserTransactions(
        domain=Domain.TESTING,
        plaid=plaid_client,
        db=walter_db,
        metrics=datadog_metrics,
    )


def test_get_task_args_success(
    sync_user_transactions_workflow: SyncUserTransactions,
) -> None:
    user_id = "user-001"
    item_id = "item-001"
    task_event = _create_task_event(user_id, item_id)
    task_args = sync_user_transactions_workflow._get_task_args(task_event)
    assert task_args == (user_id, item_id)


def test_verify_user_exists_success(
    sync_user_transactions_workflow: SyncUserTransactions,
    walter_db: WalterDB,
) -> None:
    user_id = "user-001"
    user = sync_user_transactions_workflow._verify_user_exists(user_id)
    assert user is not None
    assert user.user_id == user_id


def test_verify_user_does_not_exist(
    sync_user_transactions_workflow: SyncUserTransactions,
    walter_db: WalterDB,
) -> None:
    user_id = "user-ghost"
    # TODO: Should probably raise a custom exception here.
    with pytest.raises(ValueError):
        sync_user_transactions_workflow._verify_user_exists(user_id)


def test_verify_account_exists_success(
    sync_user_transactions_workflow: SyncUserTransactions,
    walter_db: WalterDB,
) -> None:
    user_id = "user-001"
    plaid_item_id = "plaid-item-001"
    accounts: List[Account] = sync_user_transactions_workflow._verify_accounts_exist(
        user_id, plaid_item_id
    )
    assert len(accounts) == 1
    account = accounts[0]
    assert account.account_id == "acct-001"
    assert account.user_id == user_id
    assert account.plaid_item_id == plaid_item_id
    assert account.plaid_account_id is not None
    assert account.plaid_access_token is not None


def test_verify_account_does_not_exist(
    sync_user_transactions_workflow: SyncUserTransactions,
    walter_db: WalterDB,
) -> None:
    user_id = "user-001"
    plaid_item_id = "plaid-item-ghost"
    # TODO: Should probably raise a custom exception here.
    with pytest.raises(ValueError):
        sync_user_transactions_workflow._verify_accounts_exist(user_id, plaid_item_id)


def test_get_plaid_access_token(
    sync_user_transactions_workflow: SyncUserTransactions,
    walter_db: WalterDB,
) -> None:
    user_id = "user-001"
    plaid_item_id = "plaid-item-001"
    accounts: List[Account] = sync_user_transactions_workflow._verify_accounts_exist(
        user_id, plaid_item_id
    )
    token = sync_user_transactions_workflow._get_plaid_access_token(accounts)
    assert token is not None
    assert token != ""


def test_sync_transactions_success(
    sync_user_transactions_workflow: SyncUserTransactions,
    walter_db: WalterDB,
) -> None:
    user_id = "user-001"
    plaid_item_id = "plaid-item-001"
    task_event: dict = _create_task_event(user_id, plaid_item_id)
    response: WorkflowResponse = sync_user_transactions_workflow.execute(task_event)
    assert response.name == SyncUserTransactions.WORKFLOW_NAME
    assert response.status == WorkflowStatus.SUCCESS
    assert response.data is not None
    data = response.data
    assert data["user_id"] == user_id
    assert data["plaid_item_id"] == plaid_item_id
    assert len(data["accounts"]) == 1


def _create_task_event(user_id: str, plaid_item_id: str) -> dict:
    return {
        "Records": [
            {
                "body": json.dumps(
                    {
                        "user_id": user_id,
                        "plaid_item_id": plaid_item_id,
                    }
                )
            }
        ]
    }
