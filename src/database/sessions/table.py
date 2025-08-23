import json
from dataclasses import dataclass
from typing import List, Optional

from src.aws.dynamodb.client import WalterDDBClient
from src.database.sessions.models import Session
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class SessionsTable:
    """Sessions Table"""

    TABLE_NAME_FORMAT = "Sessions-{domain}"

    ddb: WalterDDBClient
    domain: Domain

    table_name: str = None  # set during post-init

    def __post_init__(self) -> None:
        self.table_name = self.TABLE_NAME_FORMAT.format(domain=self.domain.value)
        log.debug(f"Initializing Sessions Table with name '{self.table_name}'")

    def create_session(
        self,
        user_id: str,
        token_id: str,
        ip_address: str,
        device: str,
    ) -> Session:
        args = {
            "user_id": user_id,
            "token_id": token_id,
            "ip_address": ip_address,
            "device": device,
        }
        log.info(f"Creating new session for user '{user_id}'")
        log.debug(f"Session args:\n{json.dumps(args, indent=4)}")
        session = Session.create(
            user_id=user_id,
            token_id=token_id,
            ip_address=ip_address,
            device=device,
        )
        self.ddb.put_item(self.table_name, session.to_ddb_item())
        log.info("Session created successfully!")
        return session

    def get_session(self, user_id: str, token_id: str) -> Optional[Session]:
        log.info(f"Getting session '{token_id}' for user '{user_id}'")
        item = self.ddb.get_item(
            self.table_name, SessionsTable._get_primary_key(user_id, token_id)
        )
        if item is None:
            log.info(f"Session '{token_id}' not found!")
            return None
        return Session.from_ddb_item(item)

    def get_sessions(self, user_id: str) -> List[Session]:
        log.info(f"Getting all sessions for user '{user_id}'")
        items = self.ddb.query(
            self.table_name, SessionsTable._get_sessions_by_user_key(user_id)
        )
        log.info(f"Found {len(items)} session(s) for user!")
        return [Session.from_ddb_item(item) for item in items]

    def update_session(self, session: Session) -> Session:
        log.info(f"Updating session '{session.token_id}' for user '{session.user_id}'")
        self.ddb.put_item(self.table_name, session.to_ddb_item())
        log.info(f"Session '{session.token_id}' put successfully!")
        return session

    def delete_session(self, user_id: str, token_id: str) -> None:
        log.info(f"Deleting session '{token_id}' for user '{user_id}'")
        self.ddb.delete_item(
            table=self.table_name,
            key=SessionsTable._get_primary_key(user_id, token_id),
        )
        log.info(f"Session '{token_id}' deleted successfully!")

    @staticmethod
    def _get_primary_key(user_id: str, token_id: str) -> dict:
        return {
            "user_id": {"S": user_id},
            "token_id": {"S": token_id},
        }

    @staticmethod
    def _get_sessions_by_user_key(user_id: str) -> dict:
        return {
            "user_id": {
                "AttributeValueList": [{"S": user_id}],
                "ComparisonOperator": "EQ",
            }
        }
