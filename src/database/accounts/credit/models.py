import datetime as dt
import uuid

from src.database.accounts.models import Account


class CreditAccount(Account):
    """
    WalterDB: CreditAccount model

    This model represents a user's credit account such
    as a credit card or a loan.
    """

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

    def to_dict(self) -> dict:
        return self._get_common_attributes_dict()

    def to_ddb_item(self) -> dict:
        return self._get_common_attributes_ddb_item()

    @classmethod
    def create_new_credit_account(
        cls,
        user_id: str,
        bank_name: str,
        account_name: str,
        account_last_four_numbers: str,
        balance: float,
    ):
        now = dt.datetime.now(dt.UTC)
        new_credit_account_id = str(uuid.uuid4())
        return CreditAccount(
            user_id=CreditAccount.get_user_id_key(user_id),
            account_id=CreditAccount.get_account_id_key(new_credit_account_id),
            bank_name=bank_name,
            account_name=account_name,
            account_last_four_numbers=account_last_four_numbers,
            balance=balance,
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def get_account_from_ddb_item(cls, ddb_item: dict):
        return CreditAccount(
            user_id=ddb_item["user_id"]["S"],
            account_id=ddb_item["account_id"]["S"],
            bank_name=ddb_item["bank_name"]["S"],
            account_name=ddb_item["account_name"]["S"],
            account_last_four_numbers=ddb_item["account_last_four_numbers"]["S"],
            balance=float(ddb_item["balance"]["N"]),
            created_at=dt.datetime.fromisoformat(ddb_item["created_at"]["S"]),
            updated_at=dt.datetime.fromisoformat(ddb_item["updated_at"]["S"]),
        )
