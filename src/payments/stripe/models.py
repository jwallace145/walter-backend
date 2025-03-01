from dataclasses import dataclass
from enum import Enum


class PaymentStatus(Enum):
    """
    The possible payment statuses for Stripe checkout sessions.
    """

    PAID = "paid"
    UNPAID = "unpaid"
    PENDING = "pending"


@dataclass(frozen=True)
class NewsletterSubscriptionOffering:
    """
    Stripe Newsletter Subscription Offering
    """

    PRODUCT_NAME = "Walter's Weekly Newsletter"
    PRODUCT_DESCRIPTION = "Stay informed with Walter's curated newsletter, powered by AI, delivering insightful updates and recommendations tailored for your portfolio each week."

    cents_per_month: int

    def to_dict(self) -> dict:
        return {
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": NewsletterSubscriptionOffering.PRODUCT_NAME,
                    "description": NewsletterSubscriptionOffering.PRODUCT_DESCRIPTION,
                },
                "recurring": {"interval": "month"},
                "unit_amount": self.cents_per_month,
            },
            "quantity": 1,
        }
