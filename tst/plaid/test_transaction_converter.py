import datetime as dt

import pytest

from src.database.client import WalterDB
from src.database.transactions.models import BankTransaction
from src.plaid.transaction_converter import TransactionConverter

PLAID_TRANSACTION = {
    "account_id": "plaid-acct-001",
    "account_owner": None,
    "amount": 6.33,
    "authorized_date": dt.date(2025, 8, 29),
    "authorized_datetime": None,
    "category": None,
    "category_id": None,
    "check_number": None,
    "counterparties": [
        {
            "confidence_level": "VERY_HIGH",
            "entity_id": "eyg8o776k0QmNgVpAmaQj4WgzW9Qzo6O51gdd",
            "logo_url": "https://plaid-merchant-logos.plaid.com/uber_1060.png",
            "name": "Uber",
            "phone_number": None,
            "type": "merchant",
            "website": "uber.com",
        }
    ],
    "date": dt.date(2025, 8, 30),
    "datetime": None,
    "iso_currency_code": "USD",
    "location": {
        "address": None,
        "city": None,
        "country": None,
        "lat": None,
        "lon": None,
        "postal_code": None,
        "region": None,
        "store_number": None,
    },
    "logo_url": "https://plaid-merchant-logos.plaid.com/uber_1060.png",
    "merchant_entity_id": "eyg8o776k0QmNgVpAmaQj4WgzW9Qzo6O51gdd",
    "merchant_name": "Uber",
    "name": "Uber 072515 SF**POOL**",
    "payment_channel": "online",
    "payment_meta": {
        "by_order_of": None,
        "payee": None,
        "payer": None,
        "payment_method": None,
        "payment_processor": None,
        "ppd_id": None,
        "reason": None,
        "reference_number": None,
    },
    "pending": False,
    "pending_transaction_id": None,
    "personal_finance_category": {
        "confidence_level": "VERY_HIGH",
        "detailed": "TRANSPORTATION_TAXIS_AND_RIDE_SHARES",
        "primary": "TRANSPORTATION",
    },
    "personal_finance_category_icon_url": "https://plaid-category-icons.plaid.com/PFC_TRANSPORTATION.png",
    "transaction_code": None,
    "transaction_id": "plaid-txn-001",
    "transaction_type": "special",
    "unofficial_currency_code": None,
    "website": "uber.com",
}


@pytest.fixture
def transaction_converter(walter_db: WalterDB) -> TransactionConverter:
    return TransactionConverter(walter_db)


def test_transaction_converter(transaction_converter: TransactionConverter) -> None:
    transaction = transaction_converter.convert(PLAID_TRANSACTION)

    assert isinstance(transaction, BankTransaction)
    assert transaction.plaid_account_id == "plaid-acct-001"
    assert transaction.plaid_transaction_id == "plaid-txn-001"
    assert transaction.account_id == "acct-001"
    assert transaction.merchant_name == "Uber"
    assert transaction.transaction_amount == 6.33
    assert transaction.get_transaction_date() == dt.datetime.strptime(
        "2025-08-30", "%Y-%m-%d"
    )
