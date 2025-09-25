from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

import requests

from src.ai.mlp.expenses import ExpenseCategorizerMLP
from src.database.accounts.models import Account
from src.database.client import WalterDB
from src.database.transactions.models import (
    BankingTransactionSubType,
    BankTransaction,
    Transaction,
    TransactionType,
)
from src.media.bucket import MediaBucket
from src.plaid.models import PersonalFinanceCategories
from src.utils.log import Logger

LOG = Logger(__name__).get_logger()

PERSONAL_FINANCE_CATEGORY_TO_TRANSACTION_TYPE: Dict[
    PersonalFinanceCategories, TransactionType
] = {
    PersonalFinanceCategories.ENTERTAINMENT: TransactionType.BANKING,
    PersonalFinanceCategories.FOOD_AND_DRINK: TransactionType.BANKING,
    PersonalFinanceCategories.GENERAL_MERCHANDISE: TransactionType.BANKING,
    PersonalFinanceCategories.GENERAL_SERVICES: TransactionType.BANKING,
    PersonalFinanceCategories.INCOME: TransactionType.BANKING,
    PersonalFinanceCategories.LOAN_PAYMENTS: TransactionType.BANKING,
    PersonalFinanceCategories.PERSONAL_CARE: TransactionType.BANKING,
    PersonalFinanceCategories.TRANSPORTATION: TransactionType.BANKING,
    PersonalFinanceCategories.TRAVEL: TransactionType.BANKING,
    PersonalFinanceCategories.OTHER: TransactionType.BANKING,
    PersonalFinanceCategories.TRANSFER_OUT: TransactionType.BANKING,
}
"""(dict): Mapping of personal finance categories to transaction types"""


class TransactionConversionType(Enum):
    """Transaction Conversion Types"""

    NEW = "new"
    UPDATED = "updated"
    DELETED = "deleted"


@dataclass(kw_only=True)
class TransactionConverter:
    """
    Transaction Converter

    This class is responsible for converting transactions from the Plaid API to
    WalterDB format. WalterBackend receives Plaid transactions via the SyncTransactions
    API and webhooks. These events contain new, updated, and deleted transactions. This
    converter class handles the appropriate conversion logic for each transaction type
    to ensure consistently with WalterDB and valid database logic.
    """

    db: WalterDB
    transaction_categorizer: ExpenseCategorizerMLP
    media_bucket: MediaBucket

    plaid_account_cache: Dict[str, Account] = None
    plaid_transaction_cache: Dict[str, Transaction] = None

    def __post_init__(self) -> None:
        LOG.debug("Initializing Transaction Converter")
        self.plaid_account_cache = {}
        self.plaid_transaction_cache = {}

    def convert(
        self, plaid_transaction: dict, conversion_type: TransactionConversionType
    ) -> Transaction:
        LOG.info(
            f"Converting Plaid '{conversion_type.value}' transaction to WalterDB format:\n{plaid_transaction}"
        )

        # verify account exists before converting transaction, each transaction
        # should be associated with an account persisted in the database
        plaid_account_id: str = plaid_transaction["account_id"]
        account: Account = self._verify_account_exists(plaid_account_id)

        match conversion_type:
            case TransactionConversionType.NEW:
                # For each new transaction, upload new merchant logos to media bucket
                # so WalterBackend can serve the logos from CDN with low-latency
                merchant_logo_s3_uri: Optional[str] = (
                    self._upload_merchant_logo_if_not_present(plaid_transaction)
                )

                # fall back to using account logo if merchant logo for particular transaction
                # cannot be found
                if merchant_logo_s3_uri is None:
                    merchant_logo_s3_uri = account.logo_s3_uri

                return self._create_new_transaction(
                    account, plaid_transaction, merchant_logo_s3_uri
                )
            case TransactionConversionType.UPDATED:
                transaction: Transaction = self._get_existing_transaction(
                    account, plaid_transaction
                )

                # update transaction fields
                transaction.transaction_amount = plaid_transaction["amount"]
                transaction.merchant_name = self._get_merchant_name(plaid_transaction)
                transaction.update_transaction_date(plaid_transaction["date"])

                return transaction
            case TransactionConversionType.DELETED:
                return self._get_existing_transaction(account, plaid_transaction)
            case _:
                raise ValueError(f"Unknown conversion type: {conversion_type}")

    def _verify_account_exists(self, plaid_account_id: str) -> Account:
        # if account exists in cache, return it and don't query database again
        if plaid_account_id in self.plaid_account_cache:
            return self.plaid_account_cache[plaid_account_id]

        LOG.debug(
            f"Verifying account with Plaid account ID '{plaid_account_id}' exists"
        )

        # attempt to get account from database
        account = self.db.get_account_by_plaid_account_id(plaid_account_id)

        # throw exception if account not found
        if account is None:
            LOG.error(
                f"Account with Plaid account ID '{plaid_account_id}' does not exist"
            )
            raise Exception(
                f"Account with Plaid account ID '{plaid_account_id}' does not exist"
            )

        LOG.debug(f"Account with Plaid account ID '{plaid_account_id}' exists")

        # write plaid_account_id to account_id mapping to cache
        self.plaid_account_cache[plaid_account_id] = account

        # get transactions for account only when first encountering the account from the transaction
        self._cache_account_transactions(account)

        return account

    def _cache_account_transactions(self, account: Account) -> List[Transaction]:
        LOG.debug(
            f"Getting transactions for account '{account.account_id}' to cache for Plaid transaction ID mappings"
        )
        transactions: List[Transaction] = self.db.get_transactions_by_account(
            account.account_id
        )
        # add plaid transaction id to transaction mapping to cache
        for transaction in transactions:
            self.plaid_transaction_cache[transaction.plaid_transaction_id] = transaction
        LOG.debug(
            f"Found {len(transactions)} transactions for account '{account.account_id}'"
        )
        return transactions

    def _create_new_transaction(
        self, account: Account, plaid_transaction: dict, merchant_logo_s3_uri: str
    ) -> Transaction:
        amount = plaid_transaction["amount"]

        # plaid merchant name is nullable
        merchant_name = self._get_merchant_name(plaid_transaction)

        transaction_category = self.transaction_categorizer.categorize(
            merchant_name, amount
        )

        transaction_subtype = BankingTransactionSubType.DEBIT
        if amount < 0:
            transaction_subtype = BankingTransactionSubType.CREDIT

        return BankTransaction.create(
            account_id=account.account_id,
            user_id=account.user_id,
            transaction_type=TransactionType.BANKING,
            transaction_subtype=transaction_subtype,
            transaction_category=transaction_category,
            transaction_date=plaid_transaction["date"],
            transaction_amount=amount,
            merchant_name=merchant_name,
            merchant_logo_s3_uri=merchant_logo_s3_uri,
            plaid_transaction_id=plaid_transaction["transaction_id"],
            plaid_account_id=plaid_transaction["account_id"],
        )

    def _get_existing_transaction(
        self, account: Account, plaid_transaction: dict
    ) -> Transaction:
        plaid_transaction_id: str = plaid_transaction["transaction_id"]

        if plaid_transaction_id not in self.plaid_transaction_cache:
            raise ValueError(
                "Transaction ID is required to update or delete a transaction"
            )

        transaction: Transaction = self.plaid_transaction_cache[plaid_transaction_id]

        if transaction.account_id != account.account_id:
            raise ValueError("Transaction must be associated with the same account")

        return transaction

    def _get_merchant_name(self, plaid_transaction: dict) -> str:
        # merchant name is nullable
        merchant: str = plaid_transaction.get("merchant_name", "UNKNOWN MERCHANT")
        if merchant is None:
            merchant = "UNKNOWN MERCHANT"

        name: str = plaid_transaction.get("name", "UNKNOWN_NAME")
        if name is None:
            name = "UNKNOWN_NAME"

        if merchant != "UNKNOWN MERCHANT":
            return merchant

        if name != "UNKNOWN_NAME":
            return name

        return "UNKNOWN"

    def _upload_merchant_logo_if_not_present(
        self, plaid_transaction: dict
    ) -> Optional[str]:
        LOG.debug(
            "Attempting to upload new Plaid merchant logo to media bucket if not already present..."
        )

        # logos can be null, so just skip upload if not present and transaction will use default logo
        logo_url: Optional[str] = plaid_transaction.get("logo_url", None)
        if logo_url is None:
            LOG.debug("Merchant logo URL is null, skipping upload")
            return None

        LOG.debug(
            f"Merchant logo URL is not null, checking media bucket for logo: '{logo_url}'"
        )

        logo_name = logo_url.split("/")[-1]
        logo_key = f"logos/{logo_name}"
        get_logo_resp: Tuple[bool, Optional[str]] = (
            self.media_bucket.does_public_file_exist(logo_key)
        )
        logo_exists, s3_uri = get_logo_resp

        if logo_exists:
            LOG.debug(
                f"Logo '{logo_name}' already exists in media bucket, skipping upload"
            )
            return s3_uri

        LOG.debug(f"Logo '{logo_name}' does not exist in media bucket, uploading...")

        resp = requests.get(logo_url)
        resp.raise_for_status()
        body = resp.content

        s3_uri = self.media_bucket.upload_public_contents(
            name=logo_key,
            contents=body,
        )

        LOG.debug(f"Logo '{logo_name}' uploaded successfully!")

        return s3_uri
