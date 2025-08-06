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
        return {
            **self.account.to_dict(),
            **self.transaction.to_dict(),
        }
