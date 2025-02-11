import pytest

from src.api.common.models import HTTPStatus, Status
from src.api.verify_email import VerifyEmail
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from tst.api.utils import get_verify_email_event, get_expected_response

#############
# CONSTANTS #
#############

USER_EMAIL = "walter@gmail.com"
"""(str): The email of a test user to verify."""

###########
# FIXTURE #
###########


@pytest.fixture
def verify_email_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
) -> VerifyEmail:
    return VerifyEmail(
        walter_authenticator=walter_authenticator,
        walter_cw=walter_cw,
        walter_db=walter_db,
    )


#########
# TESTS #
#########


def test_verify_email_success(
    verify_email_api: VerifyEmail,
    walter_authenticator: WalterAuthenticator,
    walter_db: WalterDB,
) -> None:
    user = walter_db.get_user(USER_EMAIL)
    user.verified = False
    walter_db.update_user(user)
    assert walter_db.get_user(USER_EMAIL).verified is False
    token = walter_authenticator.generate_email_token(USER_EMAIL)
    event = get_verify_email_event(token)
    expected_response = get_expected_response(
        api_name=verify_email_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.SUCCESS,
        message="Successfully verified email!",
    )
    assert expected_response == verify_email_api.invoke(event)
    assert walter_db.get_user(USER_EMAIL).verified is True


def test_verify_email_failure_invalid_token(
    verify_email_api: VerifyEmail,
    walter_authenticator: WalterAuthenticator,
    walter_db: WalterDB,
) -> None:
    user = walter_db.get_user(USER_EMAIL)
    user.verified = False
    walter_db.update_user(user)
    assert walter_db.get_user(USER_EMAIL).verified is False
    token = "invalid-email-verification-token"
    event = get_verify_email_event(token)
    expected_response = get_expected_response(
        api_name=verify_email_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Not authenticated!",
    )
    assert expected_response == verify_email_api.invoke(event)
    assert walter_db.get_user(USER_EMAIL).verified is False


def test_verify_email_failure_email_already_verified(
    verify_email_api: VerifyEmail,
    walter_authenticator: WalterAuthenticator,
    walter_db: WalterDB,
) -> None:
    assert walter_db.get_user(USER_EMAIL).verified is True
    token = walter_authenticator.generate_email_token(USER_EMAIL)
    event = get_verify_email_event(token)
    expected_response = get_expected_response(
        api_name=verify_email_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="User already verified!",
    )
    assert expected_response == verify_email_api.invoke(event)
    assert walter_db.get_user(USER_EMAIL).verified is True
