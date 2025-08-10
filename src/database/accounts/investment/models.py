import datetime as dt
import uuid
from typing import List

from src.database.portfolio.models import Portfolio
from src.database.accounts.models import Account
from src.utils.log import Logger

log = Logger(__name__).get_logger()


class InvestmentAccount(Account):
    """
    WalterDB: InvestmentAccount model
    """

    portfolios: List[Portfolio]

    def __init__(
        self,
        user_id: str,
        account_id: str,
        bank_name: str,
        account_name: str,
        account_last_four_numbers: str,
        balance: float,
        created_at: dt.datetime,
        updated_at: dt.datetime,
        portfolios: List[Portfolio],
        logo_url: str = Account.DEFAULT_LOGO_URL,
    ) -> None:
        super().__init__(
            user_id,
            account_id,
            bank_name,
            account_name,
            account_last_four_numbers,
            balance,
            created_at,
            updated_at,
            logo_url,
        )
        self.portfolios = portfolios

    def to_dict(self) -> dict:
        return {
            **self._get_common_attributes_dict(),
            "portfolios": [portfolio.to_dict() for portfolio in self.portfolios],
        }

    def to_ddb_item(self) -> dict:
        return self._get_common_attributes_ddb_item()

    @classmethod
    def create_new_investment_account(
        cls,
        user_id: str,
        bank_name: str,
        account_name: str,
        account_last_four_numbers: str,
        balance: float,
    ):
        now = dt.datetime.now(dt.UTC)
        new_investment_account_id = str(uuid.uuid4())
        return InvestmentAccount(
            user_id=Account.get_user_id_key(user_id),
            account_id=Account.get_account_id_key(new_investment_account_id),
            bank_name=bank_name,
            account_name=account_name,
            account_last_four_numbers=account_last_four_numbers,
            balance=balance,
            created_at=now,
            updated_at=now,
            portfolios=[],
        )

    @classmethod
    def get_account_from_ddb_item(cls, ddb_item: dict):
        return InvestmentAccount(
            user_id=ddb_item["user_id"]["S"],
            account_id=ddb_item["account_id"]["S"],
            bank_name=ddb_item["bank_name"]["S"],
            account_name=ddb_item["account_name"]["S"],
            account_last_four_numbers=ddb_item["account_last_four_numbers"]["S"],
            balance=float(ddb_item["balance"]["N"]),
            created_at=dt.datetime.fromisoformat(ddb_item["created_at"]["S"]),
            updated_at=dt.datetime.fromisoformat(ddb_item["updated_at"]["S"]),
            portfolios=[],
        )
