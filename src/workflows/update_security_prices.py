from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from src.database.client import WalterDB
from src.database.securities.models import Crypto, SecurityType, Stock
from src.polygon.client import PolygonClient
from src.utils.log import Logger
from src.workflows.common.models import (Workflow, WorkflowResponse,
                                         WorkflowStatus)

log = Logger(__name__).get_logger()


@dataclass
class UpdateSecurityPrices(Workflow):
    """
    Update Security Prices
    """

    WORKFLOW_NAME = "UpdateSecurityPrices"

    walter_db: WalterDB
    polygon: PolygonClient

    def __init__(self, walter_db: WalterDB, polygon: PolygonClient) -> None:
        super().__init__(UpdateSecurityPrices.WORKFLOW_NAME)
        self.walter_db = walter_db
        self.polygon = polygon

    def execute(self, event: dict) -> WorkflowResponse:
        log.info("Getting all securities from database")
        securities = self.walter_db.get_securities()

        log.info("Getting prices for all securities")
        updated_securities = []
        for security in securities:
            now = datetime.now(timezone.utc)
            if security.price_expires_at > now:
                log.info(
                    f"Price '${security.current_price}' for security '{security.security_id}' has not expired yet. Skipping."
                )
                continue

            log.info(f"Getting price for security '{security.security_id}'")

            price = None
            if isinstance(security, Stock):
                price = self.polygon.get_latest_price(
                    security.ticker,
                    SecurityType.STOCK,
                )
            elif isinstance(security, Crypto):
                price = self.polygon.get_latest_price(
                    security.ticker,
                    SecurityType.CRYPTO,
                )
            else:
                raise ValueError(f"Invalid security type '{security.security_type}'!")

            log.info(f"Price for security '{security.security_id}': {price}")
            security.current_price = price
            now = datetime.now(timezone.utc)
            security.price_updated_at = now
            security.price_expires_at = now + timedelta(minutes=15)
            updated_securities.append(security)

        log.info("Updating security prices in database")
        for security in updated_securities:
            log.info(f"Updating security '{security.security_id}'")
            self.walter_db.update_security(security)

        return WorkflowResponse(
            name=UpdateSecurityPrices.WORKFLOW_NAME,
            status=WorkflowStatus.SUCCESS,
            message="Security prices updated successfully",
            data={
                "num_securities": len(updated_securities),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "securities": [security.to_dict() for security in updated_securities],
            },
        )
