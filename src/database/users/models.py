import json
from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    email: str
    username: str
    password_hash: str
    salt: str

    def __dict__(self) -> dict:
        return {
            "email": self.email,
            "username": self.username,
            "password_hash": self.password_hash,
            "salt": self.salt,
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
            "salt": {"S": self.salt},
        }
