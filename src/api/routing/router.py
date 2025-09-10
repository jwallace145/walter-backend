import json
from dataclasses import dataclass

from src.api.common.methods import WalterAPIMethod
from src.api.methods import (
    add_transaction_api,
    create_account_api,
    create_link_token_api,
    create_user_api,
    delete_account_api,
    delete_transaction_api,
    edit_transaction_api,
    exchange_public_token_api,
    get_accounts_api,
    get_transactions_api,
    get_user_api,
    login_api,
    logout_api,
    refresh_api,
    sync_transactions_api,
    update_account_api,
    update_user_api,
)
from src.api.routing.methods import HTTPMethod
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class APIRouter:
    """Router for Walter API methods"""

    LOGIN_RESOURCE = "/auth/login"
    REFRESH_RESOURCE = "/auth/refresh"
    LOGOUT_RESOURCE = "/auth/logout"
    USER_RESOURCE = "/users"
    ACCOUNTS_RESOURCE = "/accounts"
    TRANSACTIONS_RESOURCE = "/transactions"
    PLAID_CREATE_LINK_TOKEN_RESOURCE = "/plaid/create-link-token"
    PLAID_EXCHANGE_PUBLIC_TOKEN_RESOURCE = "/plaid/exchange-public-token"
    PLAID_SYNC_TRANSACTIONS_RESOURCE = "/plaid/sync-transactions"

    @staticmethod
    def get_method(event: dict) -> WalterAPIMethod:
        log.debug(f"Received event:\n{json.dumps(event, indent=4)}")
        api_path = APIRouter._get_api_path(event)
        http_method = APIRouter._get_http_method(event)
        log.info(f"API path: {api_path}, HTTP method: {http_method}")

        match (api_path, http_method):

            ##################
            # AUTHENTICATION #
            ##################

            case (APIRouter.LOGIN_RESOURCE, HTTPMethod.POST):
                return login_api
            case (APIRouter.REFRESH_RESOURCE, HTTPMethod.POST):
                return refresh_api
            case (APIRouter.LOGOUT_RESOURCE, HTTPMethod.POST):
                return logout_api

            ############
            # ACCOUNTS #
            ############

            case (APIRouter.ACCOUNTS_RESOURCE, HTTPMethod.GET):
                return get_accounts_api
            case (APIRouter.ACCOUNTS_RESOURCE, HTTPMethod.POST):
                return create_account_api
            case (APIRouter.ACCOUNTS_RESOURCE, HTTPMethod.PUT):
                return update_account_api
            case (APIRouter.ACCOUNTS_RESOURCE, HTTPMethod.DELETE):
                return delete_account_api

            ################
            # TRANSACTIONS #
            ################

            case (APIRouter.TRANSACTIONS_RESOURCE, HTTPMethod.GET):
                return get_transactions_api
            case (APIRouter.TRANSACTIONS_RESOURCE, HTTPMethod.POST):
                return add_transaction_api
            case (APIRouter.TRANSACTIONS_RESOURCE, HTTPMethod.PUT):
                return edit_transaction_api
            case (APIRouter.TRANSACTIONS_RESOURCE, HTTPMethod.DELETE):
                return delete_transaction_api

            #########
            # USERS #
            #########

            case (APIRouter.USER_RESOURCE, HTTPMethod.GET):
                return get_user_api
            case (APIRouter.USER_RESOURCE, HTTPMethod.POST):
                return create_user_api
            case (APIRouter.USER_RESOURCE, HTTPMethod.PUT):
                return update_user_api

            #########
            # PLAID #
            #########

            case (APIRouter.PLAID_CREATE_LINK_TOKEN_RESOURCE, HTTPMethod.POST):
                return create_link_token_api
            case (APIRouter.PLAID_EXCHANGE_PUBLIC_TOKEN_RESOURCE, HTTPMethod.POST):
                return exchange_public_token_api
            case (APIRouter.PLAID_SYNC_TRANSACTIONS_RESOURCE, HTTPMethod.POST):
                return sync_transactions_api

            # if none of the above cases match, raise an exception as the API method is not found
            case _:
                raise Exception("API method not found!")

    @staticmethod
    def _get_api_path(event: dict) -> str:
        return event["path"]

    @staticmethod
    def _get_http_method(event: dict) -> HTTPMethod:
        return HTTPMethod.from_string(event["httpMethod"])
