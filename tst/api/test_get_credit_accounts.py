import pytest

from src.api.common.models import HTTPStatus, Status
from src.api.accounts.credit.get_credit_accounts import GetCreditAccounts
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from tst.api.utils import get_get_credit_accounts_event


@pytest.fixture
def get_credit_accounts_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
) -> GetCreditAccounts:
    return GetCreditAccounts(walter_authenticator, walter_cw, walter_db)


def test_get_credit_accounts_success(
    get_credit_accounts_api: GetCreditAccounts, jwt_walter: str
) -> None:
    get_credit_accounts_event = get_get_credit_accounts_event(jwt_walter)
    get_credit_accounts_response = get_credit_accounts_api.invoke(
        get_credit_accounts_event
    )
    assert get_credit_accounts_response.api_name == "GetCreditAccounts"
    assert get_credit_accounts_response.http_status == HTTPStatus.OK
    assert get_credit_accounts_response.status == Status.SUCCESS
    assert (
        get_credit_accounts_response.message
        == "Successfully retrieved credit accounts!"
    )
    assert get_credit_accounts_response.data.get("credit_accounts") is not None
    assert len(get_credit_accounts_response.data.get("credit_accounts")) == 1
