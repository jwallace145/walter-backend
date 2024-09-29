from src.database.users.models import User
from src.database.userstocks.models import UserStock
from src.database.userstocks.table import UsersStocksTable

################
# USERS STOCKS #
################

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

#########
# TESTS #
#########


def test_get_user_stocks(users_stocks_table: UsersStocksTable) -> None:
    walter_stocks = users_stocks_table.get_stocks_for_user(WALTER)
    walrus_stocks = users_stocks_table.get_stocks_for_user(WALRUS)
    assert set(walter_stocks) == set(WALTER_STOCKS)
    assert set(walrus_stocks) == set(WALRUS_STOCKS)
