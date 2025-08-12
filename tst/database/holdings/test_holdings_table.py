import datetime as dt

import pytest

from src.aws.dynamodb.client import WalterDDBClient
from src.database.holdings.models import Holding
from src.database.holdings.table import HoldingsTable
from src.environment import Domain
from tst.constants import HOLDINGS_TABLE_NAME


@pytest.fixture
def holdings_table(ddb_client) -> HoldingsTable:
    ddb = WalterDDBClient(ddb_client)
    return HoldingsTable(ddb=ddb, domain=Domain.TESTING)


def test_table_name_format(holdings_table: HoldingsTable):
    assert holdings_table.table_name == HOLDINGS_TABLE_NAME


def test_get_holding_seeded_items(holdings_table: HoldingsTable):
    # Seeded by MockDDB from tst/database/data/holdings.jsonl
    h1 = holdings_table.get_holding("acct-002", "sec-nasdaq-appl")
    assert isinstance(h1, Holding)
    assert h1.account_id == "acct-002"
    assert h1.security_id == "sec-nasdaq-appl"
    assert h1.quantity == pytest.approx(100.0)
    assert h1.total_cost_basis == pytest.approx(1000.0)
    assert h1.average_cost_basis == pytest.approx(10.0)
    assert isinstance(h1.created_at, dt.datetime)
    assert isinstance(h1.updated_at, dt.datetime)

    h2 = holdings_table.get_holding("acct-002", "sec-crypto-btc")
    assert isinstance(h2, Holding)
    assert h2.security_id == "sec-crypto-btc"
    assert h2.quantity == pytest.approx(250.0)
    assert h2.average_cost_basis == pytest.approx(4.0)


def test_get_holdings_for_account(holdings_table: HoldingsTable):
    holdings = holdings_table.get_holdings("acct-002")
    # Two entries in the seed file for this account
    assert isinstance(holdings, list)
    assert len(holdings) == 2
    ids = {h.security_id for h in holdings}
    assert ids == {"sec-nasdaq-appl", "sec-crypto-btc"}


def test_get_holding_not_found(holdings_table: HoldingsTable):
    result = holdings_table.get_holding("acct-not-exist", "sec-not-exist")
    assert result is None


def test_create_update_delete_holding(holdings_table: HoldingsTable):
    # Create a new holding
    new_holding = Holding.create_new_holding(
        account_id="acct-0001",
        security_id="sec-test-xyz",
        quantity=10.0,
        average_cost_basis=5.0,
    )
    created = holdings_table.create_holding(new_holding)
    assert isinstance(created, Holding)

    # Verify it can be retrieved
    fetched = holdings_table.get_holding("acct-0001", "sec-test-xyz")
    assert isinstance(fetched, Holding)
    assert fetched.account_id == "acct-0001"
    assert fetched.security_id == "sec-test-xyz"
    assert fetched.quantity == pytest.approx(10.0)
    assert fetched.total_cost_basis == pytest.approx(50.0)
    assert fetched.average_cost_basis == pytest.approx(5.0)

    # Update: change quantity and cost basis, ensure updated_at is bumped
    before_updated_at = fetched.updated_at
    fetched.quantity = 12.5
    fetched.average_cost_basis = 6.0
    fetched.total_cost_basis = fetched.quantity * fetched.average_cost_basis

    updated = holdings_table.update_holding(fetched)
    assert isinstance(updated, Holding)

    fetched2 = holdings_table.get_holding("acct-0001", "sec-test-xyz")
    assert fetched2.quantity == pytest.approx(12.5)
    assert fetched2.average_cost_basis == pytest.approx(6.0)
    assert fetched2.total_cost_basis == pytest.approx(75.0)
    assert (
        fetched2.created_at == fetched.created_at
    )  # created_at should remain the same
    assert (
        fetched2.updated_at >= before_updated_at
    )  # updated_at should be newer or equal (monotonic)

    # Delete and verify removal
    holdings_table.delete_holding("acct-0001", "sec-test-xyz")
    assert holdings_table.get_holding("acct-0001", "sec-test-xyz") is None
