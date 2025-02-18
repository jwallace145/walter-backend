import json
from dataclasses import dataclass
import datetime as dt


@dataclass
class User:
    email: str
    username: str
    password_hash: str
    sign_up_date: dt.datetime = dt.datetime.now(dt.UTC)
    last_active_date: dt.datetime = dt.datetime.now(dt.UTC)
    verified: bool = False
    subscribed: bool = True

    def __eq__(self, other) -> bool:
        if isinstance(other, User):
            return (
                self.email == other.email
                and self.username == other.username
                and self.password_hash == other.password_hash
                and self.verified == other.verified
                and self.subscribed == other.subscribed
            )
        return False

    def __dict__(self) -> dict:
        return {
            "email": self.email,
            "username": self.username,
            "password_hash": self.password_hash,
            "sign_up_date": self.sign_up_date.isoformat(),
            "last_active_date": self.last_active_date.isoformat(),
            "verified": self.verified,
            "subscribed": self.subscribed,
        }

    def __str__(self) -> str:
        return json.dumps(
            self.__dict__(),
            indent=4,
        )

    def to_ddb_item(self) -> dict:
        return {
            "email": {
                "S": self.email,
            },
            "username": {"S": self.username},
            "password_hash": {"S": self.password_hash},
            "sign_up_date": {"S": self.sign_up_date.isoformat()},
            "last_active_date": {"S": self.last_active_date.isoformat()},
            "verified": {"BOOL": self.verified},
            "subscribed": {"BOOL": self.subscribed},
        }
