from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from polygon.exceptions import BadResponse
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.securities.models import SecurityType
from src.polygon.client import PolygonClient


@pytest.fixture
def mock_rest_client(monkeypatch):
    """Fixture that mocks the RESTClient class"""
    mock_client_instance = Mock()
    mock_rest_client_class = Mock(return_value=mock_client_instance)

    monkeypatch.setattr("src.polygon.client.RESTClient", mock_rest_client_class)

    return mock_client_instance, mock_rest_client_class


@pytest.fixture
def polygon_client(
    walter_sm: WalterSecretsManagerClient,
) -> PolygonClient:
    return PolygonClient(walter_sm)


def test_get_stock_ticker_info_success(mock_rest_client, polygon_client) -> None:
    mock_client_instance, mock_rest_client_class = mock_rest_client

    # setup mock get_ticker_details response
    mock_ticker_details = Mock()
    mock_ticker_details.ticker = "AAPL"
    mock_ticker_details.name = "Apple Inc."
    mock_client_instance.get_ticker_details.return_value = mock_ticker_details

    result = polygon_client.get_ticker_info("AAPL", SecurityType.STOCK)

    mock_rest_client_class.assert_called_once_with(api_key="test-polygon-api-key")
    mock_client_instance.get_ticker_details.assert_called_once_with("AAPL")
    assert result.ticker == "AAPL"
    assert result.name == "Apple Inc."


def test_get_crypto_ticker_info_success(mock_rest_client, polygon_client) -> None:
    mock_client_instance, mock_rest_client_class = mock_rest_client

    # setup mock get_ticker_details response
    mock_ticker_details = Mock()
    mock_ticker_details.ticker = "BTC"
    mock_ticker_details.name = "Bitcoin"
    mock_client_instance.get_ticker_details.return_value = mock_ticker_details

    result = polygon_client.get_ticker_info("BTC", SecurityType.CRYPTO)

    mock_rest_client_class.assert_called_once_with(api_key="test-polygon-api-key")
    mock_client_instance.get_ticker_details.assert_called_once_with("X:BTCUSD")
    assert result.ticker == "BTC"
    assert result.name == "Bitcoin"


def test_get_latest_price_stock_success(mock_rest_client, polygon_client) -> None:
    mock_client_instance, mock_rest_client_class = mock_rest_client

    # setup mock list_aggs response with two aggregate entries
    agg1 = Mock()
    agg1.open = 100.0
    agg2 = Mock()
    agg2.open = 105.5
    mock_client_instance.list_aggs.return_value = [agg1, agg2]

    start_date = datetime(2025, 8, 14, 0, 0, 0, tzinfo=timezone.utc)
    end_date = datetime(2025, 8, 15, 0, 0, 0, tzinfo=timezone.utc)

    result = polygon_client.get_latest_price(
        "AAPL", SecurityType.STOCK, start_date=start_date, end_date=end_date
    )

    mock_rest_client_class.assert_called_once_with(api_key="test-polygon-api-key")
    mock_client_instance.list_aggs.assert_called_once_with(
        "AAPL", 1, "hour", start_date, end_date, adjusted="true", sort="asc"
    )
    assert result == 105.5


def test_get_latest_price_crypto_success(mock_rest_client, polygon_client) -> None:
    mock_client_instance, mock_rest_client_class = mock_rest_client

    # setup mock list_aggs response with three aggregate entries
    agg1 = Mock()
    agg1.open = 25000.0
    agg2 = Mock()
    agg2.open = 25250.0
    agg3 = Mock()
    agg3.open = 25100.0
    mock_client_instance.list_aggs.return_value = [agg1, agg2, agg3]

    start_date = datetime(2025, 8, 14, 12, 0, 0, tzinfo=timezone.utc)
    end_date = datetime(2025, 8, 15, 12, 0, 0, tzinfo=timezone.utc)

    result = polygon_client.get_latest_price(
        "BTC", SecurityType.CRYPTO, start_date=start_date, end_date=end_date
    )

    mock_rest_client_class.assert_called_once_with(api_key="test-polygon-api-key")
    mock_client_instance.list_aggs.assert_called_once_with(
        "X:BTCUSD", 1, "hour", start_date, end_date, adjusted="true", sort="asc"
    )
    assert result == 25100.0


def test_get_ticker_info_nonexistent_security(mock_rest_client, polygon_client) -> None:
    mock_client_instance, mock_rest_client_class = mock_rest_client

    # setup mock get_ticker_details to raise BadResponse
    mock_client_instance.get_ticker_details.side_effect = BadResponse(
        "Ticker not found"
    )

    with pytest.raises(BadResponse):
        polygon_client.get_ticker_info("NONEXISTENT", SecurityType.STOCK)

    mock_rest_client_class.assert_called_once_with(api_key="test-polygon-api-key")
    mock_client_instance.get_ticker_details.assert_called_once_with("NONEXISTENT")


def test_get_ticker() -> None:
    assert PolygonClient._get_ticker("AAPL", SecurityType.STOCK) == "AAPL"
    assert PolygonClient._get_ticker("MSFT", SecurityType.STOCK) == "MSFT"
    assert PolygonClient._get_ticker("BTC", SecurityType.CRYPTO) == "X:BTCUSD"
    assert PolygonClient._get_ticker("ETH", SecurityType.CRYPTO) == "X:ETHUSD"
