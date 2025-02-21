import pytest

from src.api.common.methods import Status, HTTPStatus
from src.api.get_stock import GetStock
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.database.stocks.models import Stock
from src.stocks.client import WalterStocksAPI
from tst.api.utils import get_get_stock_event, get_expected_response

MSFT = Stock(
    symbol="MSFT",
    company="Microsoft Corporation",
    description="Microsoft Corporation is an American multinational technology company which produces computer software, consumer electronics, personal computers, and related services. Its best known software products are the Microsoft Windows line of operating systems, the Microsoft Office suite, and the Internet Explorer and Edge web browsers. Its flagship hardware products are the Xbox video game consoles and the Microsoft Surface lineup of touchscreen personal computers. Microsoft ranked No. 21 in the 2020 Fortune 500 rankings of the largest United States corporations by total revenue; it was the world's largest software maker by revenue as of 2016. It is considered one of the Big Five companies in the U.S. information technology industry, along with Google, Apple, Amazon, and Facebook.",
    exchange="NASDAQ",
    sector="TECHNOLOGY",
    industry="SERVICES-PREPACKAGED SOFTWARE",
    official_site="https://www.microsoft.com",
    address="ONE MICROSOFT WAY, REDMOND, WA, US",
)

TEAM = Stock(
    symbol="TEAM",
    company="Atlassian Corp Plc",
    description="Atlassian Corporation Plc designs, develops, licenses and maintains various software products worldwide. The company is headquartered in Sydney, Australia.",
    exchange="NASDAQ",
    sector="TECHNOLOGY",
    industry="SERVICES-PREPACKAGED SOFTWARE",
    official_site="https://www.atlassian.com",
    address="350 BUSH STREET, FLOOR 13, SAN FRANCISCO, CA, US",
)


@pytest.fixture
def get_stock_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
    walter_stocks_api: WalterStocksAPI,
    walter_sm: WalterSecretsManagerClient,
) -> GetStock:
    return GetStock(walter_authenticator, walter_cw, walter_db, walter_stocks_api)


def test_get_stock_success_exists_in_db(
    get_stock_api: GetStock, walter_db: WalterDB
) -> None:
    event = get_get_stock_event(symbol=MSFT.symbol)
    expected_response = get_expected_response(
        api_name=get_stock_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.SUCCESS,
        message="Retrieved stock details!",
        data={
            "stock": MSFT.to_dict(),
        },
    )
    assert walter_db.get_stock(MSFT.symbol) is not None
    assert expected_response == get_stock_api.invoke(event)


def test_get_stock_success_does_not_exist_in_db(
    get_stock_api: GetStock, walter_db: WalterDB
) -> None:
    event = get_get_stock_event(symbol=TEAM.symbol)
    expected_response = get_expected_response(
        api_name=get_stock_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.SUCCESS,
        message="Retrieved stock details!",
        data={
            "stock": TEAM.to_dict(),
        },
    )
    assert walter_db.get_stock(TEAM.symbol) is None
    assert expected_response == get_stock_api.invoke(event)
    assert walter_db.get_stock(TEAM.symbol) is not None


def test_get_stock_failure_stock_does_not_exist(get_stock_api: GetStock) -> None:
    event = get_get_stock_event(symbol="INVALID")
    expected_response = get_expected_response(
        api_name=GetStock.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Stock does not exist!",
    )
    assert expected_response == get_stock_api.invoke(event)
