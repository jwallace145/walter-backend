from src.clients import plaid, polygon_client, walter_db
from src.workflows.sync_user_transactions import SyncUserTransactions
from src.workflows.update_security_prices import UpdateSecurityPrices

update_security_prices_workflow = UpdateSecurityPrices(walter_db, polygon_client)
sync_user_transactions_workflow = SyncUserTransactions(plaid, walter_db)
