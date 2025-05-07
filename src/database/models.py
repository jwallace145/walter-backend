from dataclasses import dataclass

from src.database.cash_accounts.models import CashAccount
from src.database.transactions.models import Transaction


@dataclass
class AccountTransaction:
    """
    WalterDB: AccountTransaction Model

    The model class that represents a Transaction merged
    with its owning CashAccount.
    """

    DATE_FORMAT = "%Y-%m-%d"

    account: CashAccount
    transaction: Transaction

    def to_dict(self) -> dict:
        return {
            "account_id": self.account.get_account_id(),
            "bank_name": self.account.bank_name,
            "account_name": self.account.account_name,
            "account_type": self.account.account_type.value,
            "account_last_four_numbers": self.account.account_last_four_numbers,
            "transaction_id": self.transaction.transaction_id,
            "transaction_date": self.transaction.date.strftime(
                AccountTransaction.DATE_FORMAT
            ),
            "transaction_vendor": self.transaction.vendor,
            "transaction_amount": self.transaction.amount,
            "transaction_category": self.transaction.category.value,
            "transaction_reviewed": self.transaction.reviewed,
        }
