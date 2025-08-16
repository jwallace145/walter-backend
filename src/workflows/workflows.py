from src.clients import polygon_client, walter_db
from src.workflows.update_security_prices import UpdateSecurityPrices

update_security_prices_workflow = UpdateSecurityPrices(walter_db, polygon_client)
