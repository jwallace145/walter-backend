from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from enum import Enum


class SecurityType(Enum):
    """Security Types"""

    STOCK = "stock"
    CRYPTO = "crypto"

    @classmethod
    def from_string(cls, security_type_str: str):
        for security_type in SecurityType:
            if security_type.name.lower() == security_type_str.lower():
                return security_type
        raise ValueError(f"Invalid security type '{security_type_str}'!")


class Security(ABC):
    """Security Model"""

    def __init__(
        self,
        security_id: str,
        security_name: str,
        security_type: SecurityType,
        current_price: float,
        price_updated_at: datetime,
        price_expires_at: datetime,
    ):
        self.security_id = security_id
        self.security_name = security_name
        self.security_type = security_type
        self.current_price = current_price
        self.price_updated_at = price_updated_at
        self.price_expires_at = price_expires_at

    def _get_common_attributes_dict(self) -> dict:
        return {
            "security_id": self.security_id,
            "security_name": self.security_name,
            "security_type": self.security_type.value,
            "current_price": self.current_price,
            "price_updated_at": self.price_updated_at.isoformat(),
            "price_expires_at": self.price_expires_at.isoformat(),
        }

    def _get_common_attributes_ddb_item(self) -> dict:
        return {
            "security_id": {"S": self.security_id},
            "security_name": {"S": self.security_name},
            "security_type": {"S": self.security_type.value},
            "current_price": {"N": str(self.current_price)},
            "price_updated_at": {"S": self.price_updated_at.isoformat()},
            "price_expires_at": {"S": self.price_expires_at.isoformat()},
        }

    @abstractmethod
    def _generate_security_id(self, **kwargs) -> str:
        """Generate Security ID"""
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        pass

    @abstractmethod
    def to_ddb_item(self) -> dict:
        pass


class Stock(Security):
    """Stock Model"""

    def __init__(
        self,
        name: str,
        ticker: str,
        exchange: str,
        price: float,
        price_updated_at: datetime,
        price_expires_at: datetime,
        security_id: str = None,
    ) -> None:
        if not security_id:
            security_id = self._generate_security_id(exchange=exchange, ticker=ticker)
        super().__init__(
            security_id,
            name,
            SecurityType.STOCK,
            price,
            price_updated_at,
            price_expires_at,
        )
        self.ticker = ticker
        self.exchange = exchange

    def _generate_security_id(self, **kwargs) -> str:
        exchange = kwargs.get("exchange")
        ticker = kwargs.get("ticker")
        return f"sec-{exchange.lower()}-{ticker.lower()}"

    def to_dict(self) -> dict:
        return {
            **self._get_common_attributes_dict(),
            "ticker": self.ticker,
            "exchange": self.exchange,
        }

    def to_ddb_item(self) -> dict:
        return {
            **self._get_common_attributes_ddb_item(),
            "ticker": {"S": self.ticker},
            "exchange": {"S": self.exchange},
        }

    @classmethod
    def from_ddb_item(cls, item: dict):
        security_id = item["security_id"]["S"]
        ticker = item["ticker"]["S"]
        name = item["security_name"]["S"]
        exchange = item["exchange"]["S"]
        price = float(item["current_price"]["N"])
        price_updated_at = datetime.fromisoformat(item["price_updated_at"]["S"])
        price_expires_at = datetime.fromisoformat(item["price_expires_at"]["S"])
        return Stock(
            name,
            ticker,
            exchange,
            price,
            price_updated_at,
            price_expires_at,
            security_id,
        )

    @classmethod
    def create(cls, name: str, ticker: str, exchange: str, price: float):
        now = datetime.now(timezone.utc)
        return Stock(
            name=name,
            ticker=ticker.upper(),
            exchange=exchange,
            price=price,
            price_updated_at=now,
            price_expires_at=now + timedelta(minutes=15),
        )


class Crypto(Security):
    """Crypto Model"""

    def __init__(
        self,
        name: str,
        ticker: str,
        price: float,
        price_updated_at: datetime,
        price_expires_at: datetime,
        security_id: str = None,
    ) -> None:
        if not security_id:
            security_id = self._generate_security_id(ticker=ticker)
        super().__init__(
            security_id,
            name,
            SecurityType.CRYPTO,
            price,
            price_updated_at,
            price_expires_at,
        )
        self.ticker = ticker

    def _generate_security_id(self, **kwargs) -> str:
        ticker = kwargs.get("ticker")
        return f"sec-{SecurityType.CRYPTO.value.lower()}-{ticker.lower()}"

    def to_dict(self) -> dict:
        return {**self._get_common_attributes_dict(), "ticker": self.ticker}

    def to_ddb_item(self) -> dict:
        return {
            **self._get_common_attributes_ddb_item(),
            "ticker": {"S": self.ticker},
        }

    @classmethod
    def from_ddb_item(cls, item: dict):
        security_id = item["security_id"]["S"]
        name = item["security_name"]["S"]
        ticker = item["ticker"]["S"]
        price = float(item["current_price"]["N"])
        price_updated_at = datetime.fromisoformat(item["price_updated_at"]["S"])
        price_expires_at = datetime.fromisoformat(item["price_expires_at"]["S"])
        return Crypto(
            name, ticker, price, price_updated_at, price_expires_at, security_id
        )

    @classmethod
    def create(cls, name: str, ticker: str, price: float):
        now = datetime.now(timezone.utc)
        return Crypto(
            name=name,
            ticker=ticker.upper(),
            price=price,
            price_updated_at=now,
            price_expires_at=now + timedelta(minutes=15),
        )
