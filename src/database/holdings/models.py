from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Holding:
    """Holding Model"""

    account_id: str
    security_id: str
    quantity: float
    total_cost_basis: float
    average_cost_basis: float
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict:
        return {
            "account_id": self.account_id,
            "security_id": self.security_id,
            "quantity": self.quantity,
            "total_cost_basis": self.total_cost_basis,
            "average_cost_basis": self.average_cost_basis,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def to_ddb_item(self) -> dict:
        return {
            "account_id": {"S": self.account_id},
            "security_id": {"S": self.security_id},
            "quantity": {"N": str(self.quantity)},
            "total_cost_basis": {"N": str(self.total_cost_basis)},
            "average_cost_basis": {"N": str(self.average_cost_basis)},
            "created_at": {"S": self.created_at.isoformat()},
            "updated_at": {"S": self.updated_at.isoformat()},
        }

    @classmethod
    def create_new_holding(
        cls,
        account_id: str,
        security_id: str,
        quantity: float,
        average_cost_basis: float,
    ):
        now = datetime.now(timezone.utc)
        return Holding(
            account_id=account_id,
            security_id=security_id,
            quantity=quantity,
            total_cost_basis=quantity * average_cost_basis,
            average_cost_basis=average_cost_basis,
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def from_ddb_item(cls, ddb_item: dict):
        return Holding(
            account_id=ddb_item["account_id"]["S"],
            security_id=ddb_item["security_id"]["S"],
            quantity=float(ddb_item["quantity"]["N"]),
            total_cost_basis=float(ddb_item["total_cost_basis"]["N"]),
            average_cost_basis=float(ddb_item["average_cost_basis"]["N"]),
            created_at=datetime.fromisoformat(ddb_item["created_at"]["S"]),
            updated_at=datetime.fromisoformat(ddb_item["updated_at"]["S"]),
        )
