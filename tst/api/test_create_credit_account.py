import pytest

from src.api.common.models import HTTPStatus, Status
from src.api.credit_accounts.create_credit_account import CreateCreditAccount
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from tst.api.utils import get_create_credit_account_event


@pytest.fixture
def create_credit_account_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
) -> CreateCreditAccount:
    return CreateCreditAccount(walter_authenticator, walter_cw, walter_db)


def test_create_credit_account_success(
    create_credit_account_api: CreateCreditAccount, jwt_walter: str
) -> None:
    create_credit_account_event = get_create_credit_account_event(
        jwt_walter, "Unit Test Bank", "Unit Test Credit Account", "1234", 10_000.00
    )
    create_credit_account_response = create_credit_account_api.invoke(
        create_credit_account_event
    )
    assert create_credit_account_response.api_name == "CreateCreditAccount"
    assert create_credit_account_response.http_status == HTTPStatus.CREATED
    assert create_credit_account_response.status == Status.SUCCESS
    assert (
        create_credit_account_response.message == "Credit account created successfully!"
    )
    assert (
        create_credit_account_response.data.get("credit_account").get("account_id")
        is not None
    )  # randomly generated
    assert (
        create_credit_account_response.data.get("credit_account").get("bank_name")
        == "Unit Test Bank"
    )
    assert (
        create_credit_account_response.data.get("credit_account").get("account_name")
        == "Unit Test Credit Account"
    )
    assert (
        create_credit_account_response.data.get("credit_account").get("balance")
        == 10_000.00
    )
