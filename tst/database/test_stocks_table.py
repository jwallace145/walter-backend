from src.database.stocks.models import Stock

##########
# STOCKS #
##########

APPLE = Stock(symbol="AAPL", company="Apple")
AMAZON = Stock(symbol="AMZN", company="Amazon")
MICROSOFT = Stock(symbol="MSFT", company="Microsoft")
NETFLIX = Stock(symbol="NFLX", company="Netflix")
PAYPAL = Stock(symbol="PYPL", company="PayPal")
TESLA = Stock(symbol="TSLA", company="Tesla")

#########
# TESTS #
#########


def test_get_stock(stocks_table) -> None:
    apple = stocks_table.get_stock(APPLE.symbol)
    amazon = stocks_table.get_stock(AMAZON.symbol)
    microsoft = stocks_table.get_stock(MICROSOFT.symbol)
    netflix = stocks_table.get_stock(NETFLIX.symbol)
    paypal = stocks_table.get_stock(PAYPAL.symbol)
    assert apple == APPLE
    assert amazon == AMAZON
    assert microsoft == MICROSOFT
    assert netflix == NETFLIX
    assert paypal == PAYPAL


def test_list_stocks(stocks_table) -> None:
    stocks = stocks_table.list_stocks()
    assert set(stocks) == {APPLE, AMAZON, MICROSOFT, NETFLIX, PAYPAL}


def test_put_stock(stocks_table) -> None:
    assert stocks_table.get_stock(TESLA.symbol) is None
    stocks_table.put_stock(TESLA)
    assert stocks_table.get_stock(TESLA.symbol) == TESLA
