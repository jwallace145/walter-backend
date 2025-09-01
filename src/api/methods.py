from src.api.accounts.create_account import CreateAccount
from src.api.accounts.delete_account import DeleteAccount
from src.api.accounts.get_accounts.method import GetAccounts
from src.api.accounts.update_account import UpdateAccount
from src.api.auth.login.method import Login
from src.api.auth.logout.method import Logout
from src.api.auth.refresh.method import Refresh
from src.api.plaid.create_link_token import CreateLinkToken
from src.api.transactions.add_transaction import AddTransaction
from src.api.transactions.delete_transaction import DeleteTransaction
from src.api.transactions.edit_transaction import EditTransaction
from src.api.transactions.get_transactions.method import GetTransactions
from src.api.users.create_user import CreateUser
from src.api.users.get_user import GetUser
from src.api.users.update_user import UpdateUser
from src.clients import (
    AUTHENTICATOR,
    DATABASE,
    DATADOG,
    EXPENSE_CATEGORIZER,
    HOLDING_UPDATER,
    PLAID,
    POLYGON,
    S3,
    SECRETS,
    SECURITY_UPDATER,
)

###############
# API METHODS #
###############


# AUTHENTICATION
login_api = Login(AUTHENTICATOR, DATADOG, DATABASE, SECRETS)
refresh_api = Refresh(AUTHENTICATOR, DATADOG, DATABASE)
logout_api = Logout(AUTHENTICATOR, DATADOG, DATABASE)

# ACCOUNTS =
get_accounts_api = GetAccounts(AUTHENTICATOR, DATADOG, DATABASE)
create_account_api = CreateAccount(AUTHENTICATOR, DATADOG, DATABASE)
update_account_api = UpdateAccount(AUTHENTICATOR, DATADOG, DATABASE)
delete_account_api = DeleteAccount(AUTHENTICATOR, DATADOG, DATABASE)


# TRANSACTIONS
get_transactions_api = GetTransactions(AUTHENTICATOR, DATADOG, DATABASE)
add_transaction_api = AddTransaction(
    AUTHENTICATOR,
    DATADOG,
    DATABASE,
    EXPENSE_CATEGORIZER,
    POLYGON,
    HOLDING_UPDATER,
    SECURITY_UPDATER,
)
edit_transaction_api = EditTransaction(
    AUTHENTICATOR,
    DATADOG,
    DATABASE,
    POLYGON,
    HOLDING_UPDATER,
    SECURITY_UPDATER,
)
delete_transaction_api = DeleteTransaction(
    AUTHENTICATOR, DATADOG, DATABASE, HOLDING_UPDATER
)

# USERS
get_user_api = GetUser(AUTHENTICATOR, DATADOG, DATABASE, SECRETS, S3)
create_user_api = CreateUser(AUTHENTICATOR, DATADOG, DATABASE)
update_user_api = UpdateUser(AUTHENTICATOR, DATADOG, DATABASE, S3)

# PLAID
create_link_token_api = CreateLinkToken(AUTHENTICATOR, DATADOG, DATABASE, PLAID)
