import pytest

from src.api.common.methods import Status, HTTPStatus
from src.api.get_prices import GetPrices
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB
from src.database.stocks.models import Stock
from src.stocks.client import WalterStocksAPI
from tst.api.utils import get_get_prices_event, get_expected_response

META = Stock(
    symbol="META",
    company="Meta Platforms Inc.",
    description="Meta Platforms, Inc. develops products that enable people to connect and share with friends and family through mobile devices, PCs, virtual reality headsets, wearables and home devices around the world. The company is headquartered in Menlo Park, California.",
    exchange="NASDAQ",
    sector="TECHNOLOGY",
    industry="SERVICES-COMPUTER PROGRAMMING, DATA PROCESSING, ETC.",
    official_site="https://investor.fb.com",
    address="1601 WILLOW ROAD, MENLO PARK, CA, US",
)

ABNB = Stock(
    symbol="ABNB",
    company="Airbnb",
    exchange="NYSE",
    sector="Trade & Services",
    industry="Lodging",
    official_site="https://walterai.dev",
)


@pytest.fixture
def get_prices_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
    walter_stocks_api: WalterStocksAPI,
    walter_sm: WalterSecretsManagerClient,
) -> GetPrices:
    return GetPrices(walter_authenticator, walter_cw, walter_db, walter_stocks_api)


def test_get_prices_success_exists_in_db(
    get_prices_api: GetPrices, walter_db: WalterDB
) -> None:
    event = get_get_prices_event(symbol=META.symbol)
    expected_response = get_expected_response(
        api_name=get_prices_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.SUCCESS,
        message="Retrieved prices!",
        data={
            "stock": META.symbol,
            "prices": [
                {
                    "symbol": META.symbol,
                    "price": 200.0,
                    "timestamp": "2024-10-01T00:00:00",
                },
                {
                    "symbol": META.symbol,
                    "price": 225.0,
                    "timestamp": "2024-10-01T01:00:00",
                },
                {
                    "symbol": META.symbol,
                    "price": 250.0,
                    "timestamp": "2024-10-01T02:00:00",
                },
            ],
        },
    )
    assert walter_db.get_stock(META.symbol) is not None
    assert expected_response == get_prices_api.invoke(event)


def test_get_prices_success_does_not_exist_in_db(
    get_prices_api: GetPrices, walter_db: WalterDB
) -> None:
    event = get_get_prices_event(symbol=ABNB.symbol)
    expected_response = get_expected_response(
        api_name=get_prices_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.SUCCESS,
        message="Retrieved prices!",
        data={
            "stock": ABNB.symbol,
            "prices": [
                {
                    "symbol": ABNB.symbol,
                    "price": 1000.0,
                    "timestamp": "2024-10-01T00:00:00",
                },
                {
                    "symbol": ABNB.symbol,
                    "price": 1005.0,
                    "timestamp": "2024-10-01T01:00:00",
                },
                {
                    "symbol": ABNB.symbol,
                    "price": 1006.0,
                    "timestamp": "2024-10-01T02:00:00",
                },
            ],
        },
    )
    assert walter_db.get_stock(ABNB.symbol) is None
    assert expected_response == get_prices_api.invoke(event)
    assert walter_db.get_stock(ABNB.symbol) is not None


def test_get_prices_failure_stock_does_not_exist(
    get_prices_api: GetPrices,
    walter_db: WalterDB,
    walter_stocks_api: WalterStocksAPI,
) -> None:
    invalid_symbol = "INVALID"
    event = get_get_prices_event(symbol=invalid_symbol)
    expected_response = get_expected_response(
        api_name=get_prices_api.API_NAME,
        status_code=HTTPStatus.OK,
        status=Status.FAILURE,
        message="Stock does not exist!",
    )
    assert walter_stocks_api.get_stock(invalid_symbol) is None
    assert walter_db.get_stock(invalid_symbol) is None
    assert expected_response == get_prices_api.invoke(event)
