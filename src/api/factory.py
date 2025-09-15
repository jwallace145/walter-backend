from dataclasses import dataclass
from enum import Enum
from typing import Tuple

from src.api.accounts.create_account import CreateAccount
from src.api.accounts.delete_account import DeleteAccount
from src.api.accounts.get_accounts.method import GetAccounts
from src.api.accounts.update_account import UpdateAccount
from src.api.auth.login.method import Login
from src.api.auth.logout.method import Logout
from src.api.auth.refresh.method import Refresh
from src.api.common.methods import WalterAPIMethod
from src.api.plaid.create_link_token import CreateLinkToken
from src.api.plaid.exchange_public_token.method import ExchangePublicToken
from src.api.plaid.sync_transactions import SyncTransactions
from src.api.transactions.add_transaction import AddTransaction
from src.api.transactions.delete_transaction import DeleteTransaction
from src.api.transactions.edit_transaction import EditTransaction
from src.api.transactions.get_transactions.method import GetTransactions
from src.api.users.create_user import CreateUser
from src.api.users.get_user import GetUser
from src.api.users.update_user import UpdateUser
from src.aws.sts.client import WalterSTSClient
from src.factory import ClientFactory
from src.utils.log import Logger

LOG = Logger(__name__).get_logger()


class APIMethod(Enum):

    # AUTH
    LOGIN = Login.API_NAME
    LOGOUT = Logout.API_NAME
    REFRESH = Refresh.API_NAME

    # ACCOUNTS
    GET_ACCOUNTS = GetAccounts.API_NAME
    CREATE_ACCOUNT = CreateAccount.API_NAME
    UPDATE_ACCOUNT = UpdateAccount.API_NAME
    DELETE_ACCOUNT = DeleteAccount.API_NAME

    # TRANSACTIONS
    GET_TRANSACTIONS = GetTransactions.API_NAME
    ADD_TRANSACTION = AddTransaction.API_NAME
    EDIT_TRANSACTION = EditTransaction.API_NAME
    DELETE_TRANSACTION = DeleteTransaction.API_NAME

    # USERS
    GET_USER = GetUser.API_NAME
    CREATE_USER = CreateUser.API_NAME
    UPDATE_USER = UpdateUser.API_NAME

    # PLAID
    CREATE_LINK_TOKEN = CreateLinkToken.API_NAME
    EXCHANGE_PUBLIC_TOKEN = ExchangePublicToken.API_NAME
    SYNC_TRANSACTIONS = SyncTransactions.API_NAME

    def get_name(self) -> str:
        return self.value

    @classmethod
    def from_string(cls, method: str):
        for method_enum in cls:
            if method_enum.value == method:
                return method_enum
        raise ValueError(f"Invalid API method: {method}")


@dataclass(kw_only=True)
class APIMethodFactory:

    # API IAM role name format must stay in sync with Terraform name format for all APIs
    API_ROLE_NAME_FORMAT = "WalterBackend-API-{method}-Role-{domain}"

    client_factory: ClientFactory

    # all apis are lazily loaded after routing
    login_api: Login = None
    logout_api: Logout = None
    refresh_api: Refresh = None

    def get_api(self, api: APIMethod) -> WalterAPIMethod:
        LOG.info(f"Getting API method: '{api.value}'")

        credentials: Tuple[str, str, str] = self.get_api_credentials(api)
        aws_access_key_id, aws_secret_access_key, aws_session_token = credentials

        self.client_factory.set_aws_credentials(
            aws_access_key_id, aws_secret_access_key, aws_session_token
        )

        match api:
            case APIMethod.LOGIN:
                return Login(
                    domain=self.client_factory.get_domain(),
                    walter_authenticator=self.client_factory.get_authenticator(),
                    metrics=self.client_factory.get_metrics_client(),
                    walter_db=self.client_factory.get_db_client(),
                    walter_sm=self.client_factory.get_secrets_client(),
                )
            case APIMethod.LOGOUT:
                return Logout(
                    domain=self.client_factory.get_domain(),
                    walter_authenticator=self.client_factory.get_authenticator(),
                    metrics=self.client_factory.get_metrics_client(),
                    walter_db=self.client_factory.get_db_client(),
                )
            case APIMethod.REFRESH:
                return Refresh(
                    domain=self.client_factory.get_domain(),
                    walter_authenticator=self.client_factory.get_authenticator(),
                    metrics=self.client_factory.get_metrics_client(),
                    walter_db=self.client_factory.get_db_client(),
                )

            # ACCOUNTS
            case APIMethod.GET_ACCOUNTS:
                return GetAccounts(
                    domain=self.client_factory.get_domain(),
                    walter_authenticator=self.client_factory.get_authenticator(),
                    metrics=self.client_factory.get_metrics_client(),
                    walter_db=self.client_factory.get_db_client(),
                )
            case APIMethod.CREATE_ACCOUNT:
                return CreateAccount(
                    domain=self.client_factory.get_domain(),
                    walter_authenticator=self.client_factory.get_authenticator(),
                    metrics=self.client_factory.get_metrics_client(),
                    walter_db=self.client_factory.get_db_client(),
                )
            case APIMethod.UPDATE_ACCOUNT:
                return UpdateAccount(
                    domain=self.client_factory.get_domain(),
                    walter_authenticator=self.client_factory.get_authenticator(),
                    metrics=self.client_factory.get_metrics_client(),
                    walter_db=self.client_factory.get_db_client(),
                )
            case APIMethod.DELETE_ACCOUNT:
                return DeleteAccount(
                    domain=self.client_factory.get_domain(),
                    walter_authenticator=self.client_factory.get_authenticator(),
                    metrics=self.client_factory.get_metrics_client(),
                    walter_db=self.client_factory.get_db_client(),
                )

            # TRANSACTIONS
            case APIMethod.GET_TRANSACTIONS:
                return GetTransactions(
                    domain=self.client_factory.get_domain(),
                    walter_authenticator=self.client_factory.get_authenticator(),
                    metrics=self.client_factory.get_metrics_client(),
                    walter_db=self.client_factory.get_db_client(),
                )
            case APIMethod.ADD_TRANSACTION:
                return AddTransaction(
                    domain=self.client_factory.get_domain(),
                    walter_authenticator=self.client_factory.get_authenticator(),
                    metrics=self.client_factory.get_metrics_client(),
                    walter_db=self.client_factory.get_db_client(),
                    expense_categorizer=self.client_factory.get_expense_categorizer(),
                    polygon_client=self.client_factory.get_polygon_client(),
                    holding_updater=self.client_factory.get_holding_updater(),
                    security_updater=self.client_factory.get_security_updater(),
                )
            case APIMethod.EDIT_TRANSACTION:
                return EditTransaction(
                    domain=self.client_factory.get_domain(),
                    walter_authenticator=self.client_factory.get_authenticator(),
                    metrics=self.client_factory.get_metrics_client(),
                    walter_db=self.client_factory.get_db_client(),
                    polygon_client=self.client_factory.get_polygon_client(),
                    holding_updater=self.client_factory.get_holding_updater(),
                    security_updater=self.client_factory.get_security_updater(),
                )
            case APIMethod.DELETE_TRANSACTION:
                return DeleteTransaction(
                    domain=self.client_factory.get_domain(),
                    walter_authenticator=self.client_factory.get_authenticator(),
                    metrics=self.client_factory.get_metrics_client(),
                    walter_db=self.client_factory.get_db_client(),
                    holding_updater=self.client_factory.get_holding_updater(),
                )

            # USERS
            case APIMethod.GET_USER:
                return GetUser(
                    domain=self.client_factory.get_domain(),
                    walter_authenticator=self.client_factory.get_authenticator(),
                    metrics=self.client_factory.get_metrics_client(),
                    walter_db=self.client_factory.get_db_client(),
                    walter_sm=self.client_factory.get_secrets_client(),
                    walter_s3=self.client_factory.get_s3_client(),
                )
            case APIMethod.CREATE_USER:
                return CreateUser(
                    domain=self.client_factory.get_domain(),
                    walter_authenticator=self.client_factory.get_authenticator(),
                    metrics=self.client_factory.get_metrics_client(),
                    walter_db=self.client_factory.get_db_client(),
                )
            case APIMethod.UPDATE_USER:
                return UpdateUser(
                    domain=self.client_factory.get_domain(),
                    walter_authenticator=self.client_factory.get_authenticator(),
                    metrics=self.client_factory.get_metrics_client(),
                    walter_db=self.client_factory.get_db_client(),
                    s3_client=self.client_factory.get_s3_client(),
                )

            # PLAID
            case APIMethod.CREATE_LINK_TOKEN:
                return CreateLinkToken(
                    domain=self.client_factory.get_domain(),
                    walter_authenticator=self.client_factory.get_authenticator(),
                    metrics=self.client_factory.get_metrics_client(),
                    walter_db=self.client_factory.get_db_client(),
                    plaid=self.client_factory.get_plaid_client(),
                )
            case APIMethod.EXCHANGE_PUBLIC_TOKEN:
                return ExchangePublicToken(
                    domain=self.client_factory.get_domain(),
                    walter_authenticator=self.client_factory.get_authenticator(),
                    metrics=self.client_factory.get_metrics_client(),
                    walter_db=self.client_factory.get_db_client(),
                    plaid_client=self.client_factory.get_plaid_client(),
                    queue=self.client_factory.get_sync_transactions_task_queue(),
                )
            case APIMethod.SYNC_TRANSACTIONS:
                return SyncTransactions(
                    domain=self.client_factory.get_domain(),
                    walter_authenticator=self.client_factory.get_authenticator(),
                    metrics=self.client_factory.get_metrics_client(),
                    db=self.client_factory.get_db_client(),
                    queue=self.client_factory.get_sync_transactions_task_queue(),
                )

    def get_api_credentials(self, api: APIMethod) -> Tuple[str, str, str]:
        LOG.info(f"Getting API credentials for '{api.value}'")
        domain: str = self.client_factory.get_domain().value

        role_name = self.API_ROLE_NAME_FORMAT.format(
            method=api.get_name(), domain=domain
        )

        LOG.info(f"Assuming role '{role_name}'")
        sts: WalterSTSClient = self.client_factory.get_sts_client()
        credentials = sts.assume_role(
            role_name,
            f"{api.value}-{domain}",
        )
        LOG.info(f"Assumed role '{role_name}' successfully!")

        # get credentials from assume role response api call
        aws_access_key_id = credentials["AccessKeyId"]
        aws_secret_access_key = credentials["SecretAccessKey"]
        aws_session_token = credentials["SessionToken"]

        # return assumed role credentials
        return aws_access_key_id, aws_secret_access_key, aws_session_token
