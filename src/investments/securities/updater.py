import json
from dataclasses import dataclass

from polygon.exceptions import BadResponse
from polygon.rest.models import TickerDetails
from src.api.common.exceptions import BadRequest, SecurityDoesNotExist
from src.database.client import WalterDB
from src.database.securities.exchanges import get_market_exchange
from src.database.securities.models import Crypto, Security, SecurityType, Stock
from src.polygon.client import PolygonClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class SecurityUpdater:
    """
    Security Updater

    This class is responsible for ensuring that securities are
    valid and added to the database.
    """

    polygon_client: PolygonClient
    walter_db: WalterDB

    def __post_init__(self) -> None:
        log.debug("Initializing Security Updater")

    def add_security_if_not_exists(
        self, security_ticker: str, security_type: SecurityType
    ) -> Security:
        log.info(f"Checking for security in database with ticker '{security_ticker}'")

        existing_security = self.walter_db.get_security_by_ticker(security_ticker)
        if not existing_security:
            log.info(f"Security with ticker '{security_ticker}' not found in database")

            # raise exception if security not found in polygon
            security_details = self._verify_security_exists(
                security_ticker, security_type
            )

            new_security = None
            match security_type:
                case SecurityType.STOCK:
                    price = self.polygon_client.get_latest_price(
                        security_details.ticker.upper(), SecurityType.STOCK
                    )
                    new_security = Stock.create(
                        name=security_details.name,
                        ticker=security_details.ticker.upper(),
                        exchange=get_market_exchange(
                            security_details.primary_exchange
                        ).key_name,
                        price=price,
                    )
                case SecurityType.CRYPTO:
                    price = self.polygon_client.get_latest_price(
                        security_ticker, SecurityType.CRYPTO
                    )
                    new_security = Crypto.create(
                        name=security_details.name,
                        ticker=security_details.ticker.upper(),
                        price=price,
                    )

            log.info(
                f"Adding security with ID '{new_security.security_id}' to database"
            )
            self.walter_db.put_security(new_security)

            return new_security
        else:
            log.info(f"Security with ticker '{security_ticker}' found in database")
            return existing_security

    def _verify_security_exists(
        self, security_ticker: str, security_type: SecurityType
    ) -> TickerDetails:
        log.info(f"Verifying security exists for security_id '{security_ticker}'")
        try:
            return self.polygon_client.get_ticker_info(security_ticker, security_type)
        except BadResponse as e:
            if json.loads(str(e))["status"] == "NOT_FOUND":
                raise SecurityDoesNotExist(
                    f"Security with ticker '{security_ticker}' does not exist!"
                )
        except Exception as e:
            raise BadRequest(
                f"Error verifying security with ticker '{security_ticker}': {str(e)}"
            )
        log.info(f"Verified security exists for ticker '{security_ticker}' in Polygon!")
