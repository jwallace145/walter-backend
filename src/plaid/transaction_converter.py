from dataclasses import dataclass
from typing import Dict

from src.database.accounts.models import Account
from src.database.client import WalterDB
from src.database.transactions.models import (
    BankingTransactionSubType,
    BankTransaction,
    InvestmentTransaction,
    Transaction,
    TransactionCategory,
    TransactionType,
)
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
}
"""(dict): Mapping of personal finance categories to transaction types"""


@dataclass
class TransactionConverter:
    """
    Transaction Converter

    This class is responsible for converting transactions from the Plaid API to
    WalterDB format.
    """

    db: WalterDB

    def __post_init__(self) -> None:
        LOG.debug("Initializing Transaction Converter")

    def convert(self, plaid_transaction: dict) -> Transaction:
        # verify account exists before converting transaction, each transaction
        # should be associated with an account persisted in the database
        plaid_account_id: str = plaid_transaction["account_id"]
        account: Account = self._verify_account_exists(plaid_account_id)

        # get transaction type based on plaid category
        plaid_category: str = plaid_transaction["personal_finance_category"]["primary"]
        transaction_type: TransactionType = self._get_transaction_type(plaid_category)

        # handle transaction conversion by transaction type
        match transaction_type:
            case TransactionType.BANKING:
                return self._create_banking_transaction(account, plaid_transaction)
            case TransactionType.INVESTMENT:
                return self._create_investment_transaction(account, plaid_transaction)
            case _:
                raise ValueError(f"Unknown transaction type: {transaction_type}")

    def _verify_account_exists(self, plaid_account_id: str) -> Account:
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

        return account

    def _get_transaction_type(
        self,
        plaid_category: str,
    ) -> TransactionType:
        LOG.debug(f"Getting transaction type for Plaid category '{plaid_category}'")

        personal_finance_category = PersonalFinanceCategories.from_string(
            plaid_category
        )

        # throw exception if category mapping not found
        try:
            transaction_type = PERSONAL_FINANCE_CATEGORY_TO_TRANSACTION_TYPE[
                personal_finance_category
            ]
        except KeyError:
            raise ValueError(
                f"Invalid Plaid personal finance category '{plaid_category}'!"
            )

        LOG.debug(
            f"Transaction type for Plaid category '{plaid_category}': {transaction_type}"
        )

        return transaction_type

    def _create_banking_transaction(
        self, account: Account, plaid_transaction: dict
    ) -> BankTransaction:
        return BankTransaction.create(
            account_id=account.account_id,
            user_id=account.user_id,
            transaction_type=TransactionType.BANKING,
            transaction_subtype=BankingTransactionSubType.DEBIT,  # TODO: Fix this hardcoded value
            transaction_category=TransactionCategory.RESTAURANTS,  # TODO: Fix this hardcoded value
            transaction_date=plaid_transaction["date"],
            transaction_amount=plaid_transaction["amount"],
            merchant_name=plaid_transaction["merchant_name"],
            plaid_transaction_id=plaid_transaction["transaction_id"],
            plaid_account_id=plaid_transaction["account_id"],
        )

    def _create_investment_transaction(
        self, account: Account, plaid_transaction: dict
    ) -> InvestmentTransaction:
        # TODO: Implement investment transaction conversion
        raise NotImplementedError("Need to implement investment transaction conversion")
