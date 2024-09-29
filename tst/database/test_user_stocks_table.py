from src.database.users.models import User
from src.database.userstocks.models import UserStock
from src.database.userstocks.table import UsersStocksTable

USER = User(email="walteraifinancialadvisor@gmail.com", username="walter")
USER_STOCKS = [
    UserStock(user_email=USER.email, stock_symbol="AAPL"),
    UserStock(user_email=USER.email, stock_symbol="AMZN"),
    UserStock(user_email=USER.email, stock_symbol="MSFT"),
    UserStock(user_email=USER.email, stock_symbol="NFLX"),
    UserStock(user_email=USER.email, stock_symbol="PYPL"),
]


def test_get_user_stocks(users_stocks_table: UsersStocksTable) -> None:
    user_stocks = users_stocks_table.get_stocks_for_user(USER)
    assert set(user_stocks) == set(USER_STOCKS)
