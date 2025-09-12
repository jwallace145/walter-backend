from src.transactions.queue import (
    SyncUserTransactionsTask,
    SyncUserTransactionsTaskQueue,
)


def test_add_task_success(
    sync_transactions_task_queue: SyncUserTransactionsTaskQueue,
) -> None:
    user_id = "user-001"
    plaid_item_id = "plaid-item-001"
    task = SyncUserTransactionsTask(user_id=user_id, plaid_item_id=plaid_item_id)
    task_id = sync_transactions_task_queue.add_task(task)
    assert task_id is not None
