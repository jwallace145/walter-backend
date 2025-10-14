from dataclasses import dataclass
from typing import List

from src.database.client import WalterDB
from src.database.holdings.models import Holding
from src.database.transactions.models import (
    InvestmentTransaction,
    InvestmentTransactionSubType,
)
from src.investments.holdings.exceptions import InvalidHoldingUpdate
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class HoldingUpdater:
    """Holding Updater"""

    walter_db: WalterDB

    def __post_init__(self) -> None:
        log.debug("Initializing Holdings Updater")

    def add_transaction(self, transaction: InvestmentTransaction) -> None:
        log.info(
            f"Adding transaction '{transaction.transaction_id}' and updating holding..."
        )

        # get existing holding if one exists for user account
        holding = self.walter_db.get_holding(
            transaction.account_id, transaction.security_id
        )

        # create list of updated transactions, add existing transactions if a holding exists
        updated_transactions = []
        if holding:
            updated_transactions.extend(
                self.walter_db.get_transactions_by_holding(
                    holding.account_id, holding.security_id
                )
            )
        updated_transactions.append(transaction)

        self._update(
            transaction.account_id, transaction.security_id, updated_transactions
        )

    def update_transaction(self, transaction: InvestmentTransaction) -> None:
        log.info(
            f"Updating transaction '{transaction.transaction_id}' and updating holding..."
        )

        # get existing holding, one should exist when updating a transaction
        holding = self.walter_db.get_holding(
            transaction.account_id, transaction.security_id
        )

        # get existing transactions for holding and replace transaction to update
        transactions = self.walter_db.get_transactions_by_holding(
            holding.account_id, holding.security_id
        )

        updated_transactions = []
        for txn in transactions:
            if txn.transaction_id != transaction.transaction_id:
                updated_transactions.append(txn)
                continue
            # replace transaction to update
            updated_transactions.append(transaction)

        self._update(holding.account_id, holding.security_id, updated_transactions)

    def delete_transaction(self, transaction: InvestmentTransaction) -> None:
        log.info(
            f"Deleting transaction '{transaction.transaction_id}' and updating holding..."
        )

        # get existing holding, one should exist when deleting a transaction
        holding = self.walter_db.get_holding(
            transaction.account_id, transaction.security_id
        )

        # get existing transactions for holding and remove transaction to delete
        transactions = self.walter_db.get_transactions_by_holding(
            holding.account_id, holding.security_id
        )

        updated_transactions = []
        for txn in transactions:
            if txn.transaction_id == transaction.transaction_id:
                continue
            updated_transactions.append(txn)

        self._update(holding.account_id, holding.security_id, updated_transactions)

    def _update(
        self,
        account_id: str,
        security_id: str,
        transactions: List[InvestmentTransaction],
    ) -> None:
        log.info(
            f"Attempting to update holding for account '{account_id}' for security '{security_id}' with {len(transactions)} transactions"
        )

        # sort transactions by transaction date
        sorted_transactions = self._verify_and_sort_transactions(
            account_id, security_id, transactions
        )

        # initialize new holding with zero quantity and average cost basis to start
        updated_holding = Holding.create_new_holding(
            account_id=account_id,
            security_id=security_id,
            quantity=0,
            average_cost_basis=0,
        )

        # iterate through transaction history and update holding accordingly or throw exception
        # for invalid transaction history which will block the holding update
        for transaction in sorted_transactions:
            match transaction.transaction_subtype:
                case InvestmentTransactionSubType.BUY:
                    self._handle_buy_transaction(updated_holding, transaction)
                case InvestmentTransactionSubType.SELL:
                    self._handle_sell_transaction(updated_holding, transaction)
                case _:
                    raise InvalidHoldingUpdate(
                        f"Invalid transaction subtype: {transaction.transaction_subtype}"
                    )

        log.info("Holding update successful!")

        # handle holding with zero quantity after updating transactions
        # holding with zero quantity is invalid and should be deleted from database
        # holding with non-zero quantity is valid and should be kept in database
        if updated_holding.quantity > 0:
            self.walter_db.put_holding(updated_holding)
        else:
            log.info("Holding update resulted in zero quantity. Deleting holding...")
            self.walter_db.delete_holding(
                updated_holding.account_id, updated_holding.security_id
            )

    def _verify_and_sort_transactions(
        self,
        account_id: str,
        security_id: str,
        transactions: List[InvestmentTransaction],
    ) -> List[InvestmentTransaction]:
        for transaction in transactions:
            # ensure that all transactions are investment transactions
            if not isinstance(transaction, InvestmentTransaction):
                raise InvalidHoldingUpdate(
                    f"Transaction {transaction} is not an instance of InvestmentTransaction!"
                )

            if (
                transaction.account_id != account_id
                or transaction.security_id != security_id
            ):
                raise InvalidHoldingUpdate(
                    f"Transaction {transaction} is not associated with holding for account '{account_id}' and security '{security_id}'!"
                )

        return sorted(transactions, key=lambda t: t.transaction_date)

    def _handle_sell_transaction(
        self, holding: Holding, transaction: InvestmentTransaction
    ) -> None:
        # ensure that the holding quantity is greater than the transaction sell quantity
        if transaction.quantity > holding.quantity:
            raise InvalidHoldingUpdate(
                f"Investment transaction sell quantity ({transaction.quantity}) is greater than holding quantity ({holding.quantity})!"
            )

        # if user has enough holding quantity to satisfy sell transaction, update holding quantity and total cost basis
        # holding average cost basis does not change for sell transactions
        holding.quantity -= transaction.quantity
        holding.total_cost_basis = holding.quantity * holding.average_cost_basis

    def _handle_buy_transaction(
        self, holding: Holding, transaction: InvestmentTransaction
    ) -> None:
        holding.quantity += transaction.quantity
        holding.total_cost_basis += transaction.quantity * transaction.price_per_share
        holding.average_cost_basis = holding.total_cost_basis / holding.quantity
