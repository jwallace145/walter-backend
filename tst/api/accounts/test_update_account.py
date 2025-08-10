import json
import pytest

from src.api.accounts.update_account import UpdateAccount
from src.api.common.models import HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from tst.api.utils import get_expected_response


@pytest.fixture
def update_account_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
) -> UpdateAccount:
    return UpdateAccount(walter_authenticator, walter_cw, walter_db)


def _event_with_auth_and_body(token: str, body) -> dict:
    return {
        "headers": {
            "Authorization": f"Bearer {token}",
            "content-type": "application/json",
        },
        "queryStringParameters": None,
        "body": json.dumps(body) if not isinstance(body, str) else body,
    }


def test_update_account_success(
    update_account_api: UpdateAccount, walter_db: WalterDB, jwt_walter: str
) -> None:
    user = walter_db.get_user_by_email("walter@gmail.com")
    account = walter_db.get_accounts(user.user_id)[0]

    event = _event_with_auth_and_body(
        jwt_walter,
        {
            "account_id": account.account_id,
            "account_type": "investment",
            "account_subtype": "brokerage",
            "institution_name": "Fidelity",
            "account_name": "Taxable",
            "account_mask": "4321",
            "balance": 999.99,
            "logo_url": "https://logo.example.com",
        },
    )

    response = update_account_api.invoke(event)
    assert response.http_status == HTTPStatus.OK
    assert response.status == Status.SUCCESS
    assert response.message == "Account updated successfully!"

    updated = response.data["account"]
    assert updated["account_id"] == account.account_id
    assert updated["user_id"] == user.user_id
    assert updated["account_type"] == "investment"
    assert updated["account_subtype"] == "brokerage"
    assert updated["institution_name"] == "Fidelity"
    assert updated["account_name"] == "Taxable"
    assert updated["account_mask"] == "4321"
    assert updated["balance"] == 999.99
    assert updated["logo_url"] == "https://logo.example.com"


def test_update_account_failure_invalid_account_type(
    update_account_api: UpdateAccount, walter_db: WalterDB, jwt_walter: str
) -> None:
    user = walter_db.get_user_by_email("walter@gmail.com")
    account = walter_db.get_accounts(user.user_id)[0]
    event = _event_with_auth_and_body(
        jwt_walter,
        {
            "account_id": account.account_id,
            "account_type": "invalid-type",
            "account_subtype": "card",
            "institution_name": "Capital One",
            "account_name": "Savor",
            "account_mask": "2222",
            "balance": 10.0,
            "logo_url": "https://logo.example.com",
        },
    )
    expected_response = get_expected_response(
        api_name=update_account_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Invalid account type 'invalid-type'!",
    )
    assert expected_response == update_account_api.invoke(event)


def test_update_account_failure_account_does_not_exist(
    update_account_api: UpdateAccount, jwt_walter: str
) -> None:
    event = _event_with_auth_and_body(
        jwt_walter,
        {
            "account_id": "does-not-exist",
            "account_type": "credit",
            "account_subtype": "card",
            "institution_name": "Capital One",
            "account_name": "Savor",
            "account_mask": "2222",
            "balance": 10.0,
            "logo_url": "https://logo.example.com",
        },
    )
    expected_response = get_expected_response(
        api_name=update_account_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Account does not exist!",
    )
    assert expected_response == update_account_api.invoke(event)


def test_update_account_failure_not_authenticated(
    update_account_api: UpdateAccount, walter_db: WalterDB
) -> None:
    event = _event_with_auth_and_body(
        "invalid-token",
        {
            "account_id": "acct-123",
            "account_type": "credit",
            "account_subtype": "card",
            "institution_name": "Capital One",
            "account_name": "Savor",
            "account_mask": "2222",
            "balance": 10.0,
            "logo_url": "https://logo.example.com",
        },
    )
    expected_response = get_expected_response(
        api_name=update_account_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Not authenticated! Token is invalid.",
    )
    assert expected_response == update_account_api.invoke(event)
