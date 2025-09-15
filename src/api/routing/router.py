import json
from dataclasses import dataclass

from src.api.common.methods import WalterAPIMethod
from src.api.factory import APIMethod, APIMethodFactory
from src.api.routing.methods import HTTPMethod
from src.factory import ClientFactory
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass(kw_only=True)
class APIRouter:
    """Router for WalterBackend API methods."""

    LOGIN_RESOURCE = "/auth/login"
    REFRESH_RESOURCE = "/auth/refresh"
    LOGOUT_RESOURCE = "/auth/logout"
    USER_RESOURCE = "/users"
    ACCOUNTS_RESOURCE = "/accounts"
    TRANSACTIONS_RESOURCE = "/transactions"
    PLAID_CREATE_LINK_TOKEN_RESOURCE = "/plaid/create-link-token"
    PLAID_EXCHANGE_PUBLIC_TOKEN_RESOURCE = "/plaid/exchange-public-token"
    PLAID_SYNC_TRANSACTIONS_RESOURCE = "/plaid/sync-transactions"

    client_factory: ClientFactory

    # set during post-init
    api_factory: APIMethodFactory = None

    def __post_init__(self) -> None:
        log.debug("Initializing APIRouter")
        self.api_factory = APIMethodFactory(client_factory=self.client_factory)

    def get_method(self, event: dict) -> WalterAPIMethod:
        log.debug(f"Received event:\n{json.dumps(event, indent=4)}")
        api_path: str = self._get_api_path(event)
        http_method: HTTPMethod = self._get_http_method(event)
        log.info(f"API path: {api_path}, HTTP method: {http_method}")

        match (api_path, http_method):

            ##################
            # AUTHENTICATION #
            ##################

            case (APIRouter.LOGIN_RESOURCE, HTTPMethod.POST):
                return self.api_factory.get_api(APIMethod.LOGIN)
            case (APIRouter.REFRESH_RESOURCE, HTTPMethod.POST):
                return self.api_factory.get_api(APIMethod.REFRESH)
            case (APIRouter.LOGOUT_RESOURCE, HTTPMethod.POST):
                return self.api_factory.get_api(APIMethod.LOGOUT)

            ############
            # ACCOUNTS #
            ############

            case (APIRouter.ACCOUNTS_RESOURCE, HTTPMethod.GET):
                return self.api_factory.get_api(APIMethod.GET_ACCOUNTS)
            case (APIRouter.ACCOUNTS_RESOURCE, HTTPMethod.POST):
                return self.api_factory.get_api(APIMethod.CREATE_ACCOUNT)
            case (APIRouter.ACCOUNTS_RESOURCE, HTTPMethod.PUT):
                return self.api_factory.get_api(APIMethod.UPDATE_ACCOUNT)
            case (APIRouter.ACCOUNTS_RESOURCE, HTTPMethod.DELETE):
                return self.api_factory.get_api(APIMethod.DELETE_ACCOUNT)

            ################
            # TRANSACTIONS #
            ################

            case (APIRouter.TRANSACTIONS_RESOURCE, HTTPMethod.GET):
                return self.api_factory.get_api(APIMethod.GET_TRANSACTIONS)
            case (APIRouter.TRANSACTIONS_RESOURCE, HTTPMethod.POST):
                return self.api_factory.get_api(APIMethod.ADD_TRANSACTION)
            case (APIRouter.TRANSACTIONS_RESOURCE, HTTPMethod.PUT):
                return self.api_factory.get_api(APIMethod.EDIT_TRANSACTION)
            case (APIRouter.TRANSACTIONS_RESOURCE, HTTPMethod.DELETE):
                return self.api_factory.get_api(APIMethod.DELETE_TRANSACTION)

            #########
            # USERS #
            #########

            case (APIRouter.USER_RESOURCE, HTTPMethod.GET):
                return self.api_factory.get_api(APIMethod.GET_USER)
            case (APIRouter.USER_RESOURCE, HTTPMethod.POST):
                return self.api_factory.get_api(APIMethod.CREATE_USER)
            case (APIRouter.USER_RESOURCE, HTTPMethod.PUT):
                return self.api_factory.get_api(APIMethod.UPDATE_USER)

            #########
            # PLAID #
            #########

            case (APIRouter.PLAID_CREATE_LINK_TOKEN_RESOURCE, HTTPMethod.POST):
                return self.api_factory.get_api(APIMethod.CREATE_LINK_TOKEN)
            case (APIRouter.PLAID_EXCHANGE_PUBLIC_TOKEN_RESOURCE, HTTPMethod.POST):
                return self.api_factory.get_api(APIMethod.EXCHANGE_PUBLIC_TOKEN)
            case (APIRouter.PLAID_SYNC_TRANSACTIONS_RESOURCE, HTTPMethod.POST):
                return self.api_factory.get_api(APIMethod.SYNC_TRANSACTIONS)

            # if none of the above cases match, raise an exception as the API method is not found
            case _:
                raise Exception("API method not found!")

    def _get_api_path(self, event: dict) -> str:
        return event["path"]

    def _get_http_method(self, event: dict) -> HTTPMethod:
        return HTTPMethod.from_string(event["httpMethod"])
