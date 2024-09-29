from src.database.models import User
from src.database.userstocks.table import UsersStocksTable


def test_get_user_stocks(users_stocks_table: UsersStocksTable) -> None:
    walter = User(email="walteraifinancialadvisor@gmail.com", username="walter")
    walter_stocks = users_stocks_table.get_stocks_for_user(walter)
    assert len(walter_stocks) == 1
    assert walter_stocks[0].user_email == "walteraifinancialadvisor@gmail.com"
    assert walter_stocks[0].stock_symbol == "AAPL"
