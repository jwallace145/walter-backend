import datetime as dt
from dataclasses import dataclass
from typing import Optional


@dataclass
class PlaidItem:
    """
    Plaid Item Model
    """

    USER_ID_KEY_FORMAT = "USER_ID#{user_id}"
    ITEM_ID_KEY_FORMAT = "ITEM_ID#{item_id}"

    user_id: str
    item_id: str
    access_token: str
    institution_id: str
    institution_name: str
    created_at: dt.datetime
    cursor: Optional[str]
    synced_at: Optional[dt.datetime]

    def to_ddb_item(self) -> dict:
        ddb_item = {
            "user_id": {
                "S": self.user_id,
            },
            "item_id": {"S": self.item_id},
            "access_token": {"S": self.access_token},
            "institution_id": {"S": self.institution_id},
            "institution_name": {"S": self.institution_name},
            "created_at": {"S": self.created_at.isoformat()},
        }

        # add optional fields to return item
        if self.cursor is not None:
            ddb_item["cursor"] = {"S": self.cursor}

        if self.synced_at is not None:
            ddb_item["synced_at"] = {"S": self.synced_at.isoformat()}

        return ddb_item

    def get_user_id(self) -> str:
        return self.user_id.split("#")[1]

    def get_item_id(self) -> str:
        return self.item_id.split("#")[1]

    @staticmethod
    def get_user_id_key(user_id: str) -> str:
        return PlaidItem.USER_ID_KEY_FORMAT.format(user_id=user_id)

    @staticmethod
    def get_item_id_key(item_id: str) -> str:
        return PlaidItem.ITEM_ID_KEY_FORMAT.format(item_id=item_id)

    @classmethod
    def create_item(
        cls,
        user_id: str,
        item_id: str,
        access_token: str,
        institution_id: str,
        institution_name: str,
    ):
        return PlaidItem(
            user_id=PlaidItem.get_user_id_key(user_id),
            item_id=PlaidItem.get_item_id_key(item_id),
            access_token=access_token,
            institution_id=institution_id,
            institution_name=institution_name,
            created_at=dt.datetime.now(dt.UTC),
            cursor=None,  # cursor is set to None for new Plaid items
            synced_at=None,  # last synced at is set to None for new Plaid items
        )

    @classmethod
    def get_item_from_ddb_item(cls, ddb_item: dict):
        return PlaidItem(
            user_id=ddb_item["user_id"]["S"],
            item_id=ddb_item["item_id"]["S"],
            access_token=ddb_item["access_token"]["S"],
            institution_id=ddb_item["institution_id"]["S"],
            institution_name=ddb_item["institution_name"]["S"],
            created_at=dt.datetime.fromisoformat(ddb_item["created_at"]["S"]),
            cursor=ddb_item["cursor"]["S"] if ddb_item.get("cursor") else None,
            synced_at=(
                dt.datetime.fromisoformat(ddb_item["synced_at"]["S"])
                if ddb_item.get("synced_at")
                else None
            ),
        )
