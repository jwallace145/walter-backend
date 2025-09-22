from src.workflows.factory import WorkflowFactory, Workflows
from src.workflows.sync_user_transactions import SyncUserTransactions
from src.workflows.update_security_prices import UpdateSecurityPrices
from tst.api.utils import UNIT_TEST_REQUEST_ID


def test_workflow_factory(workflow_factory: WorkflowFactory) -> None:
    workflow = workflow_factory.get_workflow(
        Workflows.UPDATE_SECURITY_PRICES, UNIT_TEST_REQUEST_ID
    )
    assert isinstance(workflow, UpdateSecurityPrices)
    workflow = workflow_factory.get_workflow(
        Workflows.SYNC_USER_TRANSACTIONS, UNIT_TEST_REQUEST_ID
    )
    assert isinstance(workflow, SyncUserTransactions)
