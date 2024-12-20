import pytest

from src.api.create_user import CreateUser
from src.api.common.methods import Status, HTTPStatus
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.ses.client import WalterSESClient
from src.database.client import WalterDB
from src.templates.bucket import TemplatesBucket
from src.templates.engine import TemplatesEngine
from tst.api.utils import get_create_user_event, get_expected_response


@pytest.fixture
def create_user_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
    walter_ses: WalterSESClient,
    template_engine: TemplatesEngine,
    templates_bucket: TemplatesBucket,
) -> CreateUser:
    return CreateUser(
        walter_authenticator,
        walter_cw,
        walter_db,
        walter_ses,
        template_engine,
        templates_bucket,
    )


def test_create_user(create_user_api: CreateUser) -> None:
    event = get_create_user_event(email="jim@gmail.com", username="jim", password="jim")
    expected_response = get_expected_response(
        api_name=create_user_api.API_NAME,
        status_code=HTTPStatus.CREATED,
        status=Status.SUCCESS,
        message="User created!",
    )
    assert expected_response == create_user_api.invoke(event)


def test_create_user_failure_invalid_email(create_user_api: CreateUser) -> None:
    event = get_create_user_event(email="jim", username="jim", password="jim")
    expected_response = get_expected_response(
        api_name=create_user_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Invalid email!",
    )
    assert expected_response == create_user_api.invoke(event)


def test_create_user_failure_invalid_username(create_user_api: CreateUser) -> None:
    event = get_create_user_event(
        email="jim@gmail.com", username="jim ", password="jim"
    )
    expected_response = get_expected_response(
        api_name=create_user_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Invalid username!",
    )
    assert expected_response == create_user_api.invoke(event)


def test_create_user_failure_user_already_exists(create_user_api: CreateUser) -> None:
    event = get_create_user_event(
        email="walter@gmail.com", username="walter", password="walter"
    )
    expected_response = get_expected_response(
        api_name=create_user_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="User already exists!",
    )
    assert expected_response == create_user_api.invoke(event)
