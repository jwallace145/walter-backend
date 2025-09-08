from dataclasses import dataclass


@dataclass
class AccountDetails:
    """Account Details"""

    institution_id: str
    institution_name: str
    account_id: str
    account_name: str
    account_type: str
    account_subtype: str
    account_last_four_numbers: str

    def to_dict(self) -> dict:
        return {
            "institution_id": self.institution_id,
            "institution_name": self.institution_name,
            "account_id": self.account_id,
            "account_name": self.account_name,
            "account_type": self.account_type,
            "account_subtype": self.account_subtype,
            "account_last_four_numbers": self.account_last_four_numbers,
        }
