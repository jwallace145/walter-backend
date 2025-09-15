import os
from enum import Enum


class Domain(Enum):
    """WalterBackend Domains"""

    TESTING = "unittest"
    DEVELOPMENT = "dev"
    STAGING = "preprod"
    PRODUCTION = "prod"

    @classmethod
    def from_string(cls, domain_str: str):
        for domain in Domain:
            if domain.value.lower() == domain_str.lower():
                return domain
        raise ValueError(f"Unexpected domain '{domain_str}' given!")


DOMAIN = Domain.from_string(os.getenv("DOMAIN", "dev"))
"""(str): The domain of the WalterBackend service environment."""

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
"""(str): The AWS region the WalterBackend service is deployed."""
