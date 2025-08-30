import pytest

from src.database.client import WalterDB
from src.database.securities.models import Crypto, Stock
from src.environment import Domain
from src.metrics.client import DatadogMetricsClient
from src.workflows.update_security_prices import UpdateSecurityPrices
from tst.polygon.mock import MockPolygonClient


@pytest.fixture
def update_security_prices_workflow(
    walter_db: WalterDB,
    polygon_client: MockPolygonClient,
    datadog_metrics: DatadogMetricsClient,
) -> UpdateSecurityPrices:
    return UpdateSecurityPrices(
        Domain.TESTING, walter_db, polygon_client, datadog_metrics
    )


def test_update_security_prices_workflow_success(
    update_security_prices_workflow: UpdateSecurityPrices,
    walter_db: WalterDB,
) -> None:
    # assert current security prices
    securities = walter_db.get_securities()
    assert len(securities) == 5

    securities_dict = {}
    for security in securities:
        if isinstance(security, Stock) or isinstance(security, Crypto):
            securities_dict[security.security_id] = security

    assert securities_dict["sec-nasdaq-aapl"].current_price == 100.00
    assert securities_dict["sec-nyse-coke"].current_price == 250.00
    assert securities_dict["sec-nasdaq-meta"].current_price == 250.00
    assert securities_dict["sec-crypto-btc"].current_price == 50.0
    assert securities_dict["sec-crypto-eth"].current_price == 125.0

    # update security prices
    update_security_prices_workflow.invoke(event={})

    # assert updated security prices
    updated_securities = walter_db.get_securities()
    assert len(securities) == 5

    updated_securities_dict = {}
    for security in updated_securities:
        if isinstance(security, Stock) or isinstance(security, Crypto):
            updated_securities_dict[security.security_id] = security

    assert updated_securities_dict["sec-nasdaq-aapl"].current_price == 100.00
    assert updated_securities_dict["sec-nyse-coke"].current_price == 100.00
    assert updated_securities_dict["sec-nasdaq-meta"].current_price == 10000.00
    assert updated_securities_dict["sec-crypto-btc"].current_price == 10000.00
    assert updated_securities_dict["sec-crypto-eth"].current_price == 10000.00
