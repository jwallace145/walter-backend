import pytest

from src.api.get_news import GetNews
from src.api.methods import HTTPStatus, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.stocks.client import WalterStocksAPI
from tst.api.utils import get_news_event, get_expected_response


@pytest.fixture
def get_news_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
    walter_stocks_api: WalterStocksAPI,
) -> GetNews:
    return GetNews(walter_authenticator, walter_cw, walter_db, walter_stocks_api)


def test_get_news(get_news_api: GetNews) -> None:
    event = get_news_event(stock="AAPL")
    expected_response = get_expected_response(
        api_name=get_news_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.SUCCESS,
        message="Retrieved news!",
        data={"news": ["It is much bigger than Atlantis!"]},
    )
    assert expected_response == get_news_api.invoke(event)


def test_get_news_failure_stock_does_not_exist(get_news_api: GetNews) -> None:
    event = get_news_event(stock="INVALID")
    expected_response = get_expected_response(
        api_name=get_news_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Stock does not exist!",
    )
    assert expected_response == get_news_api.invoke(event)
