from datetime import datetime, timezone, timedelta
import json
from dataclasses import dataclass
from typing import Optional
import random

from src.config import CONFIG


@dataclass
class User:
    """
    Walter User Model
    """

    email: str
    first_name: str
    last_name: str
    password_hash: str
    user_id: str = None  # user primary key, set during post init as unique id
    sign_up_date: datetime = datetime.now(timezone.utc)
    last_active_date: datetime = datetime.now(timezone.utc)
    free_trial_end_date: datetime = datetime.now(timezone.utc) + timedelta(
        days=CONFIG.newsletter.free_trial_length_days
    )
    verified: bool = False
    subscribed: bool = True
    profile_picture_s3_uri: Optional[str] = None
    profile_picture_url: Optional[str] = None
    profile_picture_url_expiration: Optional[datetime] = None
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None

    def __post_init__(self) -> None:
        # if user_id is not set during instantiation, set it
        if self.user_id is None:
            self.user_id = User.generate_user_id()

    def __eq__(self, other) -> bool:
        if isinstance(other, User):
            return (
                self.email == other.email
                and self.first_name == other.first_name
                and self.last_name == other.last_name
                and self.password_hash == other.password_hash
                and self.verified == other.verified
                and self.subscribed == other.subscribed
            )
        return False

    def __dict__(self) -> dict:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "password_hash": self.password_hash,
            "sign_up_date": self.sign_up_date.isoformat(),
            "last_active_date": self.last_active_date.isoformat(),
            "free_trial_end_date": self.free_trial_end_date.isoformat(),
            "verified": self.verified,
            "subscribed": self.subscribed,
            "profile_picture_s3_uri": self.profile_picture_s3_uri,
            "profile_picture_url": self.profile_picture_url,
            "profile_picture_url_expiration": (
                self.profile_picture_url_expiration.isoformat()
                if self.profile_picture_url_expiration
                else None
            ),
            "stripe_subscription_id": self.stripe_subscription_id,
            "stripe_customer_id": self.stripe_customer_id,
        }

    def __str__(self) -> str:
        return json.dumps(
            self.__dict__(),
            indent=4,
        )

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "sign_up_date": self.sign_up_date.isoformat(),
            "last_active_date": self.last_active_date.isoformat(),
            "verified": self.verified,
        }

    def to_ddb_item(self) -> dict:
        # set default values for optional fields
        profile_picture_s3_uri = "N/A"
        if self.profile_picture_s3_uri:
            profile_picture_s3_uri = self.profile_picture_s3_uri

        profile_picture_url = "N/A"
        if self.profile_picture_url:
            profile_picture_url = self.profile_picture_url

        profile_picture_url_expiration = "N/A"
        if self.profile_picture_url_expiration and isinstance(
            self.profile_picture_url_expiration, datetime
        ):
            profile_picture_url_expiration = (
                self.profile_picture_url_expiration.isoformat()
            )

        stripe_customer_id = "N/A"
        if self.stripe_customer_id:
            stripe_customer_id = self.stripe_customer_id

        stripe_subscription_id = "N/A"
        if self.stripe_subscription_id:
            stripe_subscription_id = self.stripe_subscription_id

        # return ddb item with all fields set (even optional ones with default values)
        return {
            "user_id": {
                "S": self.user_id,
            },
            "email": {
                "S": self.email,
            },
            "first_name": {"S": self.first_name},
            "last_name": {"S": self.last_name},
            "password_hash": {"S": self.password_hash},
            "sign_up_date": {"S": self.sign_up_date.isoformat()},
            "last_active_date": {"S": self.last_active_date.isoformat()},
            "free_trial_end_date": {"S": self.free_trial_end_date.isoformat()},
            "verified": {"BOOL": self.verified},
            "subscribed": {"BOOL": self.subscribed},
            "profile_picture_s3_uri": {"S": profile_picture_s3_uri},
            "profile_picture_url": {"S": profile_picture_url},
            "profile_picture_url_expiration": {"S": profile_picture_url_expiration},
            "stripe_subscription_id": {"S": stripe_subscription_id},
            "stripe_customer_id": {"S": stripe_customer_id},
        }

    @staticmethod
    def generate_user_id() -> str:
        timestamp_part = str(int(datetime.now(timezone.utc).timestamp()))[-6:]
        random_part = str(random.randint(1000, 9999))
        return f"user-{timestamp_part}{random_part}"
