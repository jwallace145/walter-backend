import pytest

from src.aws.dynamodb.client import WalterDDBClient
from src.database.client import WalterDB
from src.database.users.models import User
from src.database.userstocks.models import UserStock
from src.environment import Domain

WALTER = User(email="walter@gmail.com", username="walter")
WALRUS = User(email="walrus@gmail.com", username="walrus")

WALTER_STOCKS = [
    UserStock(user_email=WALTER.email, stock_symbol="AAPL", quantity=1.0),
    UserStock(user_email=WALTER.email, stock_symbol="AMZN", quantity=1.5),
    UserStock(user_email=WALTER.email, stock_symbol="MSFT", quantity=2.0),
    UserStock(user_email=WALTER.email, stock_symbol="NFLX", quantity=10.0),
    UserStock(user_email=WALTER.email, stock_symbol="PYPL", quantity=10.0),
]
WALRUS_STOCKS = [
    UserStock(user_email=WALRUS.email, stock_symbol="AMZN", quantity=100.0),
    UserStock(user_email=WALRUS.email, stock_symbol="MSFT", quantity=100.0),
    UserStock(user_email=WALRUS.email, stock_symbol="NFLX", quantity=100.0),
]


@pytest.fixture
def walter_db(ddb_client) -> WalterDB:
    return WalterDB(ddb=WalterDDBClient(ddb_client), domain=Domain.TESTING)


def test_get_user(walter_db: WalterDB):
    assert WALTER == walter_db.get_user(WALTER.email)
    assert WALRUS == walter_db.get_user(WALRUS.email)


def test_get_stocks_for_user(walter_db: WalterDB):
    assert set(WALTER_STOCKS) == set(walter_db.get_stocks_for_user(WALTER).values())
    assert set(WALRUS_STOCKS) == set(walter_db.get_stocks_for_user(WALRUS).values())
