from src.workflows.update_security_prices import UpdateSecurityPrices
from src.clients import walter_db, polygon_client

update_security_prices_workflow = UpdateSecurityPrices(walter_db, polygon_client)
