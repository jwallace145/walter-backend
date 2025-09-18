from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional


@dataclass
class Session:
    """Session Model"""

    user_id: str
    token_id: str
    ip_address: str
    device: str
    session_start: datetime
    session_expiration: datetime
    revoked: bool
    session_end: Optional[datetime] = None
    ttl: Optional[int] = None

    def to_ddb_item(self) -> dict:
        ddb_item = {
            "user_id": {"S": self.user_id},
            "token_id": {"S": self.token_id},
            "ip_address": {"S": self.ip_address},
            "device": {"S": self.device},
            "session_start": {"S": self.session_start.isoformat()},
            "session_expiration": {"S": self.session_expiration.isoformat()},
            "revoked": {"BOOL": self.revoked},
        }

        # add optional fields to return item
        if self.session_end:
            ddb_item["session_end"] = {"S": self.session_end.isoformat()}

        if self.ttl:
            ddb_item["ttl"] = {"N": str(self.ttl)}

        return ddb_item

    @classmethod
    def create(
        cls,
        user_id: str,
        token_id: str,
        ip_address: str,
        device: str,
    ) -> "Session":
        now = datetime.now(timezone.utc)
        # TODO: This should stay in sync with refresh token expiry
        session_expiration = now + timedelta(days=7)
        # TODO: This should be a config value
        ttl = session_expiration + timedelta(days=7)
        return Session(
            user_id=user_id,
            token_id=token_id,
            ip_address=ip_address,
            device=device,
            session_start=now,
            session_expiration=session_expiration,
            revoked=False,
            ttl=int(ttl.timestamp()),
        )

    @classmethod
    def from_ddb_item(cls, ddb_item: dict):
        return Session(
            user_id=ddb_item["user_id"]["S"],
            token_id=ddb_item["token_id"]["S"],
            ip_address=ddb_item["ip_address"]["S"],
            device=ddb_item["device"]["S"],
            session_start=datetime.fromisoformat(ddb_item["session_start"]["S"]),
            session_expiration=datetime.fromisoformat(
                ddb_item["session_expiration"]["S"]
            ),
            revoked=ddb_item["revoked"]["BOOL"],
            session_end=ddb_item.get("session_end", {}).get("S"),
            ttl=ddb_item.get("ttl", {}).get("N"),
        )
