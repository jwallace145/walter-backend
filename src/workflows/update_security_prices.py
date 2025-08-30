from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from src.database.client import WalterDB
from src.database.securities.models import Crypto, SecurityType, Stock
from src.environment import Domain
from src.metrics.client import DatadogMetricsClient
from src.polygon.client import PolygonClient
from src.utils.log import Logger
from src.workflows.common.models import Workflow, WorkflowResponse, WorkflowStatus

log = Logger(__name__).get_logger()


@dataclass
class UpdateSecurityPrices(Workflow):
    """
    Update Security Prices
    """

    WORKFLOW_NAME = "UpdateSecurityPrices"
    METRICS_NUM_SECURITIES_METRIC = "workflow.num_securities"
    METRICS_NUM_UPDATED_SECURITIES_METRIC = "workflow.num_updated_securities"

    walter_db: WalterDB
    polygon: PolygonClient

    def __init__(
        self,
        domain: Domain,
        walter_db: WalterDB,
        polygon: PolygonClient,
        metrics: DatadogMetricsClient,
    ) -> None:
        super().__init__(UpdateSecurityPrices.WORKFLOW_NAME, domain, metrics)
        self.walter_db = walter_db
        self.polygon = polygon

    def execute(self, event: dict, emit_metrics: bool = True) -> WorkflowResponse:
        start_time = datetime.now(timezone.utc)

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

        # emit update prices specific metrics
        if emit_metrics:
            log.info(f"Emitting '{self.name}' workflow additional metrics")
            tags = self._get_metric_tags()
            self.metrics.emit_metric(
                self.METRICS_NUM_SECURITIES_METRIC, len(securities), tags
            )
            self.metrics.emit_metric(
                self.METRICS_NUM_UPDATED_SECURITIES_METRIC,
                len(updated_securities),
                tags,
            )
        else:
            log.info(f"Not emitting additional metrics for '{self.name}' workflow!")

        return WorkflowResponse(
            name=UpdateSecurityPrices.WORKFLOW_NAME,
            status=WorkflowStatus.SUCCESS,
            message="Security prices updated successfully",
            data={
                "duration_seconds": (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds(),
                "total_num_securities": len(securities),
                "updated_num_securities": len(updated_securities),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "securities": [security.to_dict() for security in updated_securities],
            },
        )
