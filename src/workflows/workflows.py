from src.clients import DATABASE, DATADOG, DOMAIN, PLAID, POLYGON
from src.workflows.sync_user_transactions import SyncUserTransactions
from src.workflows.update_security_prices import UpdateSecurityPrices

update_security_prices_workflow = UpdateSecurityPrices(
    DOMAIN, DATABASE, POLYGON, DATADOG
)

sync_user_transactions_workflow = SyncUserTransactions(DOMAIN, PLAID, DATABASE, DATADOG)
