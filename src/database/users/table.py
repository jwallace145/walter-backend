import datetime as dt
from dataclasses import dataclass
from typing import List

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
    USERNAMES_INDEX_NAME_FORMAT = "Users-UsernameIndex-{domain}"

    ddb: WalterDDBClient
    domain: Domain

    table: str = None  # set during post init
    username_index_name: str = None  # set during post init

    def __post_init__(self) -> None:
        self.table = UsersTable._get_table_name(self.domain)
        self.username_index_name = UsersTable._get_username_index_name(self.domain)
        log.debug(f"Creating UsersTable DDB client with table name '{self.table}'")

    def create_user(self, user: User) -> None:
        log.info(
            f"Creating the following user and adding to table '{self.table}':\n{user}"
        )
        item = user.to_ddb_item()
        self.ddb.put_item(self.table, item)

    def get_user(self, email: str) -> User | None:
        log.info(f"Getting user with email '{email}' from table '{self.table}'")
        key = UsersTable._get_user_key(email)
        item = self.ddb.get_item(self.table, key)
        if item is None:
            return None
        return UsersTable._get_user_from_ddb_item(item)

    def get_user_by_username(self, username: str) -> User | None:
        log.info(f"Getting user with username '{username}' from table '{self.table}'")
        expression = "username = :username"
        attributes = {":username": {"S": username}}
        item = self.ddb.query_index(
            self.table, self.username_index_name, expression, attributes
        )
        if item is None:
            return None
        return UsersTable._get_user_from_ddb_item(item)

    def update_user(self, user: User) -> None:
        log.info(f"Updating user with email '{user.email}'")
        self.ddb.put_item(self.table, user.to_ddb_item())

    def delete_user(self, email: str) -> None:
        log.info(f"Deleting user with email '{email}'")
        self.ddb.delete_item(self.table, UsersTable._get_user_key(email))

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
    def _get_username_index_name(domain: Domain) -> str:
        return UsersTable.USERNAMES_INDEX_NAME_FORMAT.format(domain=domain.value)

    @staticmethod
    def _get_user_key(email: str) -> dict:
        return {"email": {"S": email}}

    @staticmethod
    def _get_user_from_ddb_item(item: dict) -> User:
        stripe_customer_id = None
        if item["stripe_customer_id"]["S"] != "N/A":
            stripe_customer_id = item["stripe_customer_id"]["S"]
        stripe_subscription_id = None
        if item["stripe_subscription_id"]["S"] != "N/A":
            stripe_subscription_id = item["stripe_subscription_id"]["S"]
        return User(
            email=item["email"]["S"],
            username=item["username"]["S"],
            password_hash=item["password_hash"]["S"],
            last_active_date=dt.datetime.fromisoformat(item["last_active_date"]["S"]),
            sign_up_date=dt.datetime.fromisoformat(item["sign_up_date"]["S"]),
            verified=item["verified"]["BOOL"],
            subscribed=item["subscribed"]["BOOL"],
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
        )
