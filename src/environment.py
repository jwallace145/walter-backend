from enum import Enum


class Domain(Enum):

    TESTING = "unittest"
    DEVELOPMENT = "dev"
    STAGING = "preprod"
    PRODUCTION = "prod"


def get_domain(domain_str: str) -> Domain:
    for domain in Domain:
        if domain.name == domain_str:
            return domain
    raise ValueError(f"Unexpected domain '{domain_str}' given!")
