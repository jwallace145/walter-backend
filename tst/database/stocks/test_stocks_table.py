def test_list_stocks(stocks_table) -> None:
    stocks = stocks_table.list_stocks()
    assert len(stocks) == 1
    assert stocks[0].symbol == "AAPL"
    assert stocks[0].company == "Apple"
