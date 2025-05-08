from dataclasses import dataclass
import datetime as dt


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
    institution_name: str
    created_at: dt.datetime

    def to_ddb_item(self) -> dict:
        return {
            "user_id": {
                "S": self.user_id,
            },
            "item_id": {"S": self.item_id},
            "access_token": {"S": self.access_token},
            "institution_name": {"S": self.institution_name},
            "created_at": {"S": self.created_at.isoformat()},
        }

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
        institution_name: str,
    ):
        return PlaidItem(
            user_id=PlaidItem.get_user_id_key(user_id),
            item_id=PlaidItem.get_item_id_key(item_id),
            access_token=access_token,
            institution_name=institution_name,
            created_at=dt.datetime.now(dt.UTC),
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
        )
