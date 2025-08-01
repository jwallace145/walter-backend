from dataclasses import dataclass

from src.database.transactions.models import TransactionCategory


@dataclass
class MockTransactionsCategorizer:
    def categorize(self, vendor: str, amount: float) -> TransactionCategory:
        return TransactionCategory.INCOME
