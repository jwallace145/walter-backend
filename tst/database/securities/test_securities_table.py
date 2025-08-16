import datetime as dt

import pytest

from src.aws.dynamodb.client import WalterDDBClient
from src.database.securities.models import Crypto, SecurityType, Stock
from src.database.securities.table import SecuritiesTable
from src.environment import Domain
from tst.constants import SECURITIES_TABLE_NAME


@pytest.fixture
def securities_table(ddb_client) -> SecuritiesTable:
    ddb = WalterDDBClient(ddb_client)
    return SecuritiesTable(ddb=ddb, domain=Domain.TESTING)


def test_table_name_format(securities_table: SecuritiesTable):
    assert securities_table.table_name == SECURITIES_TABLE_NAME


def test_get_security_stock(securities_table: SecuritiesTable):
    # seeded by tst/conftest.py via MockDDB
    stock = securities_table.get_security("sec-nasdaq-aapl")
    assert isinstance(stock, Stock)
    assert stock.security_id == "sec-nasdaq-aapl"
    assert stock.security_type == SecurityType.STOCK
    assert stock.security_name.lower().startswith("apple")
    assert stock.ticker == "AAPL"
    assert stock.exchange == "NASDAQ"
    # price and timestamps
    assert isinstance(stock.current_price, float)
    assert stock.current_price == pytest.approx(100.0)
    assert isinstance(stock.price_updated_at, dt.datetime)
    assert isinstance(stock.price_expires_at, dt.datetime)


def test_get_security_crypto(securities_table: SecuritiesTable):
    crypto = securities_table.get_security("sec-crypto-btc")
    assert isinstance(crypto, Crypto)
    assert crypto.security_id == "sec-crypto-btc"
    assert crypto.security_type == SecurityType.CRYPTO
    assert crypto.security_name.lower() == "bitcoin"
    assert crypto.ticker == "BTC"
    # price and timestamps
    assert isinstance(crypto.current_price, float)
    assert crypto.current_price == pytest.approx(50.0)
    assert isinstance(crypto.price_updated_at, dt.datetime)
    assert isinstance(crypto.price_expires_at, dt.datetime)


def test_get_security_not_found(securities_table: SecuritiesTable):
    result = securities_table.get_security("sec-not-exist")
    assert result is None


def test_create_update_delete_security(securities_table: SecuritiesTable):
    # Create new stock
    now = dt.datetime(2025, 3, 1, tzinfo=dt.timezone.utc)
    expires = dt.datetime(2025, 3, 1, 1, tzinfo=dt.timezone.utc)
    new_stock = Stock(
        name="Test Company",
        ticker="TST",
        exchange="NYSE",
        price=10.0,
        price_updated_at=now,
        price_expires_at=expires,
    )

    created = securities_table.create_security(new_stock)
    assert isinstance(created, Stock)
    # Ensure it can be retrieved
    fetched = securities_table.get_security(created.security_id)
    assert isinstance(fetched, Stock)
    assert fetched.security_id == created.security_id
    assert fetched.ticker == "TST"
    assert fetched.exchange == "NYSE"
    assert fetched.current_price == pytest.approx(10.0)

    # Update price
    fetched.current_price = 12.34
    fetched.price_updated_at = now + dt.timedelta(minutes=30)
    fetched.price_expires_at = expires + dt.timedelta(minutes=30)
    updated = securities_table.update_security(fetched)
    assert isinstance(updated, Stock)

    # Verify update persisted
    fetched2 = securities_table.get_security(created.security_id)
    assert fetched2.current_price == pytest.approx(12.34)

    # Delete
    securities_table.delete_security(created.security_id)
    assert securities_table.get_security(created.security_id) is None
