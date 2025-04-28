from src.database.client import WalterDB
from src.database.users.models import User
from src.database.userstocks.models import UserStock

#########
# USERS #
#########

WALTER = User(
    user_id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
    email="walter@gmail.com",
    first_name="Walter",
    last_name="Walrus",
    password_hash="walter",
    verified=True,
    subscribed=True,
)

WALRUS = User(
    user_id="9b2e7e2b-661b-4e0f-b9d3-5b5f5cf4f0ab",
    email="walrus@gmail.com",
    first_name="Walrus",
    last_name="Walrus",
    password_hash="walrus",
    verified=False,
    subscribed=True,
)

###################
# USER PORTFOLIOS #
###################

WALTER_STOCKS = [
    UserStock(user_id=WALTER.user_id, stock_symbol="AAPL", quantity=1.0),
    UserStock(user_id=WALTER.user_id, stock_symbol="AMZN", quantity=1.5),
    UserStock(user_id=WALTER.user_id, stock_symbol="MSFT", quantity=2.0),
    UserStock(user_id=WALTER.user_id, stock_symbol="NFLX", quantity=10.0),
    UserStock(user_id=WALTER.user_id, stock_symbol="PYPL", quantity=10.0),
]
WALRUS_STOCKS = [
    UserStock(user_id=WALRUS.user_id, stock_symbol="AAPL", quantity=100.0),
    UserStock(user_id=WALRUS.user_id, stock_symbol="META", quantity=100.0),
]

##############
# UNIT TESTS #
##############


def test_get_user(walter_db: WalterDB):
    # TODO: deprecate get_user() in favor of get_user_by_email(), keep tests until then
    assert WALTER == walter_db.get_user(WALTER.email)
    assert WALRUS == walter_db.get_user(WALRUS.email)
    assert WALTER == walter_db.get_user_by_email(WALTER.email)
    assert WALRUS == walter_db.get_user_by_email(WALRUS.email)


def test_get_stocks_for_user(walter_db: WalterDB):
    assert set(WALTER_STOCKS) == set(walter_db.get_stocks_for_user(WALTER).values())
    assert set(WALRUS_STOCKS) == set(walter_db.get_stocks_for_user(WALRUS).values())
