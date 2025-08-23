import datetime as dt
from dataclasses import dataclass
from typing import List, Optional

from src.aws.dynamodb.client import WalterDDBClient
from src.database.users.models import User
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class UsersTable:
    """
    Users Table
    """

    TABLE_NAME_FORMAT = "Users-{domain}"
    EMAIL_INDEX_NAME_FORMAT = "Users-EmailIndex-{domain}"

    ddb: WalterDDBClient
    domain: Domain

    table: str = None  # set during post init
    email_index_name: str = None  # set during post init

    def __post_init__(self) -> None:
        self.table = UsersTable._get_table_name(self.domain)
        self.email_index_name = UsersTable._get_email_index_name(self.domain)
        log.debug(f"Creating UsersTable DDB client with table name '{self.table}'")

    def create_user(self, user: User) -> User:
        log.info(
            f"Creating the following user and adding to table '{self.table}':\n{user}"
        )
        item = user.to_ddb_item()
        self.ddb.put_item(self.table, item)
        return user

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        log.info(f"Getting user '{user_id}' from table '{self.table}'")
        key = UsersTable._get_user_key(user_id)
        item = self.ddb.get_item(self.table, key)
        if item is None:
            return None
        return UsersTable._get_user_from_ddb_item(item)

    def get_user_by_email(self, email: str) -> Optional[User]:
        log.info(f"Getting user with email '{email}' from table '{self.table}'")
        expression = "email = :email"
        attributes = {":email": {"S": email}}
        items = self.ddb.query_index(
            self.table, self.email_index_name, expression, attributes
        )
        return None if len(items) == 0 else UsersTable._get_user_from_ddb_item(items[0])

    def update_user(self, user: User) -> None:
        log.info(f"Updating user with email '{user.email}'")
        self.ddb.put_item(self.table, user.to_ddb_item())

    def delete_user(self, user_id: str) -> None:
        log.info(f"Deleting user '{user_id}'")
        self.ddb.delete_item(self.table, UsersTable._get_user_key(user_id))

    def get_users(self) -> List[User]:
        log.info(f"Getting users from table '{self.table}'")
        users = []
        for item in self.ddb.scan_table(self.table):
            users.append(UsersTable._get_user_from_ddb_item(item))
        return users

    @staticmethod
    def _get_table_name(domain: Domain) -> str:
        return UsersTable.TABLE_NAME_FORMAT.format(domain=domain.value)

    @staticmethod
    def _get_email_index_name(domain: Domain) -> str:
        return UsersTable.EMAIL_INDEX_NAME_FORMAT.format(domain=domain.value)

    @staticmethod
    def _get_user_key(user_id: str) -> dict:
        return {"user_id": {"S": user_id}}

    @staticmethod
    def _get_user_from_ddb_item(item: dict) -> User:
        # set optional fields, if not provided then set as None
        profile_picture_s3_uri = None
        if item["profile_picture_s3_uri"]["S"] != "N/A":
            profile_picture_s3_uri = item["profile_picture_s3_uri"]["S"]

        profile_picture_url = None
        if item["profile_picture_url"]["S"] != "N/A":
            profile_picture_url = item["profile_picture_url"]["S"]

        profile_picture_url_expiration = None
        if item["profile_picture_url_expiration"]["S"] != "N/A":
            profile_picture_url_expiration = dt.datetime.fromisoformat(
                item["profile_picture_url_expiration"]["S"]
            ).replace(tzinfo=dt.UTC)

        stripe_customer_id = None
        if item["stripe_customer_id"]["S"] != "N/A":
            stripe_customer_id = item["stripe_customer_id"]["S"]

        stripe_subscription_id = None
        if item["stripe_subscription_id"]["S"] != "N/A":
            stripe_subscription_id = item["stripe_subscription_id"]["S"]

        return User(
            user_id=item["user_id"]["S"],
            email=item["email"]["S"],
            first_name=item["first_name"]["S"],
            last_name=item["last_name"]["S"],
            password_hash=item["password_hash"]["S"],
            sign_up_date=dt.datetime.fromisoformat(item["sign_up_date"]["S"]),
            last_active_date=dt.datetime.fromisoformat(item["last_active_date"]["S"]),
            verified=item["verified"]["BOOL"],
            profile_picture_s3_uri=profile_picture_s3_uri,
            profile_picture_url=profile_picture_url,
            profile_picture_url_expiration=profile_picture_url_expiration,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
        )
