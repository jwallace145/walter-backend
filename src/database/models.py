from dataclasses import dataclass

from src.database.accounts.models import Account
from src.database.transactions.models import Transaction


@dataclass
class AccountTransaction:
    """
    WalterDB: AccountTransaction Model

    The model class that represents a Transaction merged
    with its owning Account.
    """

    account: Account
    transaction: Transaction

    def to_dict(self) -> dict:
        account_dict = self.account.to_dict()
        transaction_dict = self.transaction.to_dict()
        return {
            "account_id": account_dict["account_id"],
            "transaction_id": transaction_dict["transaction_id"],
            "date": transaction_dict["date"],
            "vendor": transaction_dict["vendor"],
            "amount": transaction_dict["amount"],
            "category": transaction_dict["category"],
            "reviewed": transaction_dict["reviewed"],
        }
