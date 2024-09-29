from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    email: str
    username: str

    def to_ddb_item(self) -> dict:
        return {
            "email": {
                "S": self.email,
            },
            "username": {"S": self.username},
        }
