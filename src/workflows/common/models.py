from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from src.utils.log import Logger

log = Logger(__name__).get_logger()


class WorkflowStatus(Enum):
    """Workflow Status"""

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"

    @classmethod
    def from_string(cls, status: str):
        for status_enum in cls:
            if status_enum.value.lower() == status.lower():
                return status_enum
        raise ValueError(f"{status} is not a valid status!")


@dataclass
class WorkflowResponse:
    """Workflow Response"""

    name: str
    status: WorkflowStatus
    message: str
    data: Optional[dict] = None

    def to_json(self) -> dict:
        response = {
            "Service": "WalterBackend",
            "Workflow": self.name,
            "Status": self.status.value,
            "Message": self.message,
        }

        # add optional data field to response
        if self.data:
            response["Data"] = self.data

        return response


class Workflow(ABC):
    """Workflow Base Class"""

    def __init__(self, name: str) -> None:
        self.name = name

    def invoke(self, event: dict) -> WorkflowResponse:
        log.info(f"Invoking '{self.name}' workflow!")
        return self.execute(event)

    @abstractmethod
    def execute(self, event: dict) -> WorkflowResponse:
        pass
