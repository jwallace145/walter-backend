from src.database.client import WalterDB
from src.database.users.models import User
from src.database.userstocks.models import UserStock

WALTER = User(
    email="walter@gmail.com",
    first_name="Walter",
    last_name="Walrus",
    password_hash="walter",
    verified=True,
    subscribed=True,
)
WALRUS = User(
    email="walrus@gmail.com",
    first_name="Walrus",
    last_name="Walrus",
    password_hash="walrus",
    verified=False,
    subscribed=True,
)

WALTER_STOCKS = [
    UserStock(user_email=WALTER.email, stock_symbol="AAPL", quantity=1.0),
    UserStock(user_email=WALTER.email, stock_symbol="AMZN", quantity=1.5),
    UserStock(user_email=WALTER.email, stock_symbol="MSFT", quantity=2.0),
    UserStock(user_email=WALTER.email, stock_symbol="NFLX", quantity=10.0),
    UserStock(user_email=WALTER.email, stock_symbol="PYPL", quantity=10.0),
]
WALRUS_STOCKS = [
    UserStock(user_email=WALRUS.email, stock_symbol="AAPL", quantity=100.0),
    UserStock(user_email=WALRUS.email, stock_symbol="META", quantity=100.0),
]


def test_get_user(walter_db: WalterDB):
    assert WALTER == walter_db.get_user(WALTER.email)
    assert WALRUS == walter_db.get_user(WALRUS.email)


def test_get_stocks_for_user(walter_db: WalterDB):
    assert set(WALTER_STOCKS) == set(walter_db.get_stocks_for_user(WALTER).values())
    assert set(WALRUS_STOCKS) == set(walter_db.get_stocks_for_user(WALRUS).values())
