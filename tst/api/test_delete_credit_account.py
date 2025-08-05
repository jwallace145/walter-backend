import pytest

from src.api.common.models import HTTPStatus, Status
from src.api.credit_accounts.delete_credit_account import DeleteCreditAccount
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from tst.api.utils import get_delete_credit_account_event


@pytest.fixture
def delete_credit_account_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
) -> DeleteCreditAccount:
    return DeleteCreditAccount(walter_authenticator, walter_cw, walter_db)


def test_delete_credit_account_success(
    delete_credit_account_api: DeleteCreditAccount, jwt_walrus: str
) -> None:
    # credit account id to delete located in credit_accounts.jsonl testing data
    account_id = "aiy654ns-67ss-1977-b982-1b82b2c3d750"
    delete_credit_account_event = get_delete_credit_account_event(
        token=jwt_walrus, account_id=account_id
    )
    delete_credit_account_response = delete_credit_account_api.invoke(
        delete_credit_account_event
    )
    assert delete_credit_account_response.api_name == "DeleteCreditAccount"
    assert delete_credit_account_response.http_status == HTTPStatus.OK
    assert delete_credit_account_response.status == Status.SUCCESS
    assert (
        delete_credit_account_response.message == "Successfully deleted credit account!"
    )


def test_delete_credit_account_failure_not_authenticated(
    delete_credit_account_api: DeleteCreditAccount,
) -> None:
    # credit account id to delete located in credit_accounts.jsonl testing data
    account_id = "aiy654ns-67ss-1977-b982-1b82b2c3d750"
    delete_credit_account_event = get_delete_credit_account_event(
        token="INVALID_TOKEN", account_id=account_id
    )
    delete_credit_account_response = delete_credit_account_api.invoke(
        delete_credit_account_event
    )
    assert delete_credit_account_response.api_name == "DeleteCreditAccount"
    assert delete_credit_account_response.http_status == HTTPStatus.OK
    assert delete_credit_account_response.status == Status.FAILURE
    assert (
        delete_credit_account_response.message == "Not authenticated! Token is invalid."
    )


def test_delete_credit_account_failure_account_does_not_exist(
    delete_credit_account_api: DeleteCreditAccount, jwt_walrus: str
) -> None:
    delete_credit_account_event = get_delete_credit_account_event(
        token=jwt_walrus, account_id="INVALID_CREDIT_ACCOUNT_ID"
    )
    delete_credit_account_response = delete_credit_account_api.invoke(
        delete_credit_account_event
    )
    assert delete_credit_account_response.api_name == "DeleteCreditAccount"
    assert delete_credit_account_response.http_status == HTTPStatus.OK
    assert delete_credit_account_response.status == Status.FAILURE
    assert delete_credit_account_response.message == "Credit account does not exist!"
