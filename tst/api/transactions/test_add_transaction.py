import datetime as dt
import json

import pytest

from src.ai.mlp.expenses import ExpenseCategorizerMLP
from src.api.common.models import Status, HTTPStatus
from src.api.transactions.add_transaction import AddTransaction
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.transactions.models import (
    TransactionType,
    TransactionCategory,
    InvestmentTransactionSubType,
    BankingTransactionSubType,
    BankTransaction,
)


@pytest.fixture()
def add_transaction_api(
    walter_authenticator: WalterAuthenticator,
    walter_cw: WalterCloudWatchClient,
    walter_db: WalterDB,
    transactions_categorizer: ExpenseCategorizerMLP,
):
    return AddTransaction(
        walter_authenticator, walter_cw, walter_db, transactions_categorizer
    )


def create_add_transaction_event(token: str, body: dict) -> dict:
    return {
        "resource": "/transactions",
        "path": "/transactions",
        "httpMethod": "POST",
        "headers": {
            "Authorization": f"Bearer {token}",
            "content-type": "application/json",
        },
        "queryStringParameters": None,
        "body": json.dumps(body),
    }


def test_add_bank_debit_success(
    add_transaction_api: AddTransaction, walter_db: WalterDB, jwt_walter: str
):
    event = create_add_transaction_event(
        token=jwt_walter,
        body={
            "account_id": "acct-001",
            "date": "2025-08-07",
            "amount": 12.34,
            "transaction_type": TransactionType.BANKING.value,
            "transaction_subtype": BankingTransactionSubType.DEBIT.value,
            "transaction_category": TransactionCategory.RESTAURANTS.value,
            "merchant_name": "Chipotle",
        },
    )
    response = add_transaction_api.invoke(event)
    assert response.http_status == HTTPStatus.CREATED
    assert response.status == Status.SUCCESS
    assert response.data is not None
    txn = response.data["transaction"]
    assert txn["transaction_type"] == TransactionType.BANKING.value
    assert txn["transaction_subtype"] == BankingTransactionSubType.DEBIT.value
    assert txn["transaction_category"] == TransactionCategory.RESTAURANTS.value
    assert txn["merchant_name"] == "Chipotle"
    # ensure persisted
    txn = walter_db.get_transaction(
        account_id="acct-001",
        transaction_id=txn["transaction_id"],
        transaction_date=dt.datetime.strptime("2025-08-07", "%Y-%m-%d"),
    )
    assert txn is not None
    assert isinstance(txn, BankTransaction)


def test_add_investment_buy_new_holding_success(
    add_transaction_api: AddTransaction, walter_db: WalterDB, jwt_walrus: str
):
    event = create_add_transaction_event(
        token=jwt_walrus,
        body={
            "account_id": "acct-002",
            "date": "2025-08-04",
            "amount": 500.0,
            "transaction_type": TransactionType.INVESTMENT.value,
            "transaction_subtype": InvestmentTransactionSubType.BUY.value,
            "transaction_category": TransactionCategory.INVESTMENT.value,
            "security_id": "sec-nasdaq-aapl",
            "quantity": 50,
            "price_per_share": 10,
        },
    )
    response = add_transaction_api.invoke(event)
    assert response.http_status == HTTPStatus.CREATED
    assert response.status == Status.SUCCESS
    data_txn = response.data["transaction"]
    assert data_txn["transaction_type"] == TransactionType.INVESTMENT.value
    assert data_txn["security_id"] == "sec-nasdaq-aapl"
    # holding created
    holding = walter_db.get_holding(
        account_id="acct-002", security_id="sec-nasdaq-aapl"
    )
    assert holding is not None
    assert holding.quantity == pytest.approx(50)
    assert holding.average_cost_basis == pytest.approx(10)


def test_add_investment_buy_updates_holding(
    add_transaction_api: AddTransaction, walter_db: WalterDB, jwt_walrus: str
):
    event = create_add_transaction_event(
        token=jwt_walrus,
        body={
            "account_id": "acct-002",
            "date": "2025-08-08",
            "amount": 600,
            "transaction_type": TransactionType.INVESTMENT.value,
            "transaction_subtype": InvestmentTransactionSubType.BUY.value,
            "transaction_category": TransactionCategory.INVESTMENT.value,
            "security_id": "sec-nyse-coke",
            "quantity": 4,
            "price_per_share": 150,
        },
    )
    response = add_transaction_api.invoke(event)
    assert response.status == Status.SUCCESS
    holding = walter_db.get_holding("acct-002", "sec-nyse-coke")
    assert holding.quantity == pytest.approx(8)
    assert holding.total_cost_basis == pytest.approx(1400)
    assert holding.average_cost_basis == pytest.approx(175)


def test_add_investment_sell_insufficient_quantity(
    add_transaction_api: AddTransaction, walter_db: WalterDB, jwt_walrus: str
):
    event = create_add_transaction_event(
        token=jwt_walrus,
        body={
            "account_id": "acct-002",
            "date": "2025-08-09",
            "amount": 2510.0,
            "transaction_type": TransactionType.INVESTMENT.value,
            "transaction_subtype": InvestmentTransactionSubType.SELL.value,
            "transaction_category": TransactionCategory.INVESTMENT.value,
            "security_id": "sec-crypto-btc",
            "quantity": 251.0,
            "price_per_share": 10.0,
        },
    )
    response = add_transaction_api.invoke(event)
    assert response.http_status == HTTPStatus.OK
    assert response.status == Status.FAILURE
    assert "Not enough holding" in response.message


def test_add_investment_sell_updates_holding(
    add_transaction_api: AddTransaction, walter_db: WalterDB, jwt_walrus: str
):
    event = create_add_transaction_event(
        token=jwt_walrus,
        body={
            "account_id": "acct-002",
            "date": "2025-08-09",
            "amount": 1000.00,
            "transaction_type": TransactionType.INVESTMENT.value,
            "transaction_subtype": InvestmentTransactionSubType.SELL.value,
            "transaction_category": TransactionCategory.INVESTMENT.value,
            "security_id": "sec-crypto-btc",
            "quantity": 200,
            "price_per_share": 5.0,
        },
    )
    response = add_transaction_api.invoke(event)
    assert response.status == Status.SUCCESS
    holding = walter_db.get_holding("acct-002", "sec-crypto-btc")
    assert holding.quantity == pytest.approx(50)
    assert holding.total_cost_basis == pytest.approx(200.00)
    assert holding.average_cost_basis == pytest.approx(4.0)


def test_account_not_found(add_transaction_api: AddTransaction, jwt_walrus: str):
    # account does not exist for acct-999
    event = create_add_transaction_event(
        token=jwt_walrus,
        body={
            "account_id": "acct-999",
            "date": "2025-08-07",
            "amount": 1.0,
            "transaction_type": TransactionType.BANKING.value,
            "transaction_subtype": BankingTransactionSubType.DEBIT.value,
            "transaction_category": TransactionCategory.RESTAURANTS.value,
            "merchant_name": "Cafe",
        },
    )
    response = add_transaction_api.invoke(event)
    assert response.http_status == HTTPStatus.OK
    assert response.status == Status.FAILURE
    assert "Account does not exist" in response.message


def test_invalid_account_type_for_investment(
    add_transaction_api: AddTransaction,
    walter_db: WalterDB,
    jwt_walter: str,
):
    event = create_add_transaction_event(
        token=jwt_walter,
        body={
            "account_id": "acct-001",
            "date": "2025-08-04",
            "amount": 100.0,
            "transaction_type": TransactionType.INVESTMENT.value,
            "transaction_subtype": InvestmentTransactionSubType.BUY.value,
            "transaction_category": TransactionCategory.INVESTMENT.value,
            "security_id": "sec-foo",
            "quantity": 1,
            "price_per_share": 100,
            "merchant_name": "N/A",
        },
    )
    response = add_transaction_api.invoke(event)
    assert response.http_status == HTTPStatus.OK
    assert response.status == Status.FAILURE
    assert "Account type must be investment" in response.message


def test_invalid_date_format_fails_validation(
    add_transaction_api: AddTransaction, jwt_walrus: str
):
    event = create_add_transaction_event(
        token=jwt_walrus,
        body={
            "account_id": "acct-003",
            "date": "08-07-2025",  # wrong format
            "amount": 12.34,
            "transaction_type": TransactionType.BANKING.value,
            "transaction_subtype": BankingTransactionSubType.DEBIT.value,
            "transaction_category": TransactionCategory.RESTAURANTS.value,
            "merchant_name": "Chipotle",
        },
    )
    response = add_transaction_api.invoke(event)
    assert response.http_status == HTTPStatus.OK
    assert response.status == Status.FAILURE
    assert "Invalid date format" in response.message


def test_invalid_amount_fails_validation(
    add_transaction_api: AddTransaction, jwt_walrus: str
):
    event = create_add_transaction_event(
        token=jwt_walrus,
        body={
            "account_id": "acct-003",
            "date": "2025-08-07",
            "amount": "abc",
            "transaction_type": TransactionType.BANKING.value,
            "transaction_subtype": BankingTransactionSubType.DEBIT.value,
            "transaction_category": TransactionCategory.RESTAURANTS.value,
            "merchant_name": "Chipotle",
        },
    )
    response = add_transaction_api.invoke(event)
    assert response.http_status == HTTPStatus.OK
    assert response.status == Status.FAILURE
    assert "Invalid transaction amount" in response.message


def test_investment_amount_mismatch(
    add_transaction_api: AddTransaction, jwt_walrus: str
):
    event = create_add_transaction_event(
        token=jwt_walrus,
        body={
            "account_id": "acct-002",
            "date": "2025-08-04",
            "amount": 100.01,  # should be 100.0
            "transaction_type": TransactionType.INVESTMENT.value,
            "transaction_subtype": InvestmentTransactionSubType.BUY.value,
            "transaction_category": TransactionCategory.INVESTMENT.value,
            "security_id": "sec-nyse-coke",
            "quantity": 10,
            "price_per_share": 10,
            "merchant_name": "N/A",
        },
    )
    response = add_transaction_api.invoke(event)
    assert response.http_status == HTTPStatus.OK
    assert response.status == Status.FAILURE
    assert "Amount must equal quantity * price_per_share" in response.message


def test_bank_missing_merchant_name_validation(
    add_transaction_api: AddTransaction, jwt_walrus: str
):
    event = create_add_transaction_event(
        token=jwt_walrus,
        body={
            "account_id": "acct-003",
            "date": "2025-08-07",
            "amount": 10.0,
            "transaction_type": TransactionType.BANKING.value,
            "transaction_subtype": BankingTransactionSubType.DEBIT.value,
            "transaction_category": TransactionCategory.RESTAURANTS.value,
            # merchant_name omitted
        },
    )
    response = add_transaction_api.invoke(event)
    assert response.http_status == HTTPStatus.OK
    assert response.status == Status.FAILURE
    assert "Missing required field for bank transaction" in response.message
