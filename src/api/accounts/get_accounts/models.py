from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from src.database.accounts.models import Account, AccountType, InvestmentAccount
from src.database.holdings.models import Holding
from src.database.securities.models import Security
from src.database.users.models import User


@dataclass
class GetAccountsResponseAccountDict:
    linked_with_plaid: bool
    account_id: str
    institution_name: str
    account_name: str
    account_type: AccountType
    account_subtype: str
    balance: float
    updated_at: datetime

    def to_dict(self) -> dict:
        return {
            "linked_with_plaid": self.linked_with_plaid,
            "account_id": self.account_id,
            "institution_name": self.institution_name,
            "account_name": self.account_name,
            "account_type": self.account_type.value,
            "account_subtype": self.account_subtype,
            "balance": self.balance,
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class GetAccountsResponseHoldingDict:
    security_id: str
    security_ticker: str
    security_name: str
    quantity: float
    current_price: float
    total_value: float
    total_cost_basis: float
    average_cost_basis: float
    gain_loss: float
    updated_at: datetime

    def to_dict(self) -> dict:
        return {
            "security_id": self.security_id,
            "security_ticker": self.security_ticker,
            "security_name": self.security_name,
            "quantity": self.quantity,
            "current_price": self.current_price,
            "total_value": self.total_value,
            "total_cost_basis": self.total_cost_basis,
            "average_cost_basis": self.average_cost_basis,
            "gain_loss": self.gain_loss,
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class GetAccountsResponseInvestmentAccountDict:
    linked_with_plaid: bool
    account_id: str
    institution_name: str
    account_name: str
    account_type: AccountType
    account_subtype: str
    balance: float
    updated_at: datetime
    holdings: List[GetAccountsResponseHoldingDict]

    def to_dict(self) -> dict:
        return {
            "linked_with_plaid": self.linked_with_plaid,
            "account_id": self.account_id,
            "institution_name": self.institution_name,
            "account_name": self.account_name,
            "account_type": self.account_type.value,
            "account_subtype": self.account_subtype,
            "balance": self.balance,
            "updated_at": self.updated_at.isoformat(),
            "holdings": [holding.to_dict() for holding in self.holdings],
        }


@dataclass
class GetAccountsResponseData:

    user: User
    accounts: List[Account]
    holdings: List[Holding]
    securities: List[Security]

    def __post_init__(self) -> None:
        # create a map from account_id to holdings
        self.account_to_holdings: Dict[str, List[Holding]] = {}
        for holding in self.holdings:
            if holding.account_id not in self.account_to_holdings:
                self.account_to_holdings[holding.account_id] = []
            self.account_to_holdings[holding.account_id].append(holding)

        # create a map from security_id to security
        self.security_id_to_security: Dict[str, Security] = {}
        for security in self.securities:
            self.security_id_to_security[security.security_id] = security

    def to_dict(self):
        return {
            "user_id": self.user.user_id,
            "total_num_accounts": len(self.accounts),
            "total_balance": sum([account.balance for account in self.accounts]),
            "accounts": [account.to_dict() for account in self._get_accounts()],
        }

    def _get_accounts(self) -> List[GetAccountsResponseAccountDict]:
        accounts = []
        for account in self.accounts:
            account_type = account.account_type
            if account_type == AccountType.INVESTMENT and isinstance(
                account, InvestmentAccount
            ):
                holdings = self._get_holdings(account)
                accounts.append(
                    GetAccountsResponseInvestmentAccountDict(
                        linked_with_plaid=account.is_linked_with_plaid(),
                        account_id=account.account_id,
                        institution_name=account.institution_name,
                        account_name=account.account_name,
                        account_type=account.account_type,
                        account_subtype=account.account_subtype,
                        balance=sum([holding.total_value for holding in holdings]),
                        updated_at=account.updated_at,
                        holdings=holdings,
                    )
                )
            else:
                accounts.append(
                    GetAccountsResponseAccountDict(
                        linked_with_plaid=account.is_linked_with_plaid(),
                        account_id=account.account_id,
                        institution_name=account.institution_name,
                        account_name=account.account_name,
                        account_type=account.account_type,
                        account_subtype=account.account_subtype,
                        balance=account.balance,
                        updated_at=account.updated_at,
                    )
                )
        return accounts

    def _get_holdings(
        self, account: InvestmentAccount
    ) -> List[GetAccountsResponseHoldingDict]:
        # check if the account has holdings
        if account.account_id not in self.account_to_holdings:
            return []

        # get the holdings for the account
        account_holdings: List[Holding] = self.account_to_holdings[account.account_id]

        # iterate over the holdings for the account and create a list of dictionaries
        holdings: List[GetAccountsResponseHoldingDict] = []
        for holding in account_holdings:
            security: Security = self.security_id_to_security[holding.security_id]
            holdings.append(
                GetAccountsResponseHoldingDict(
                    security_id=holding.security_id,
                    security_ticker=security.ticker,
                    security_name=security.security_name,
                    quantity=holding.quantity,
                    current_price=security.current_price,
                    total_value=holding.quantity * security.current_price,
                    total_cost_basis=holding.total_cost_basis,
                    average_cost_basis=holding.average_cost_basis,
                    gain_loss=holding.quantity * security.current_price
                    - holding.total_cost_basis,
                    updated_at=holding.updated_at,
                )
            )

        return holdings

    @classmethod
    def create(
        cls,
        user: User,
        accounts: List[Account],
        holdings: List[Holding],
        securities: List[Security],
    ):
        return GetAccountsResponseData(
            user,
            accounts,
            holdings,
            securities,
        )
