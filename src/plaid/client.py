from dataclasses import dataclass

from plaid import ApiClient, Configuration
from plaid.api.plaid_api import PlaidApi
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products

from src.plaid.models import CreateLinkTokenResponse, ExchangePublicTokenResponse
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class PlaidClient:
    """
    Plaid Client
    """

    CLIENT_NAME = "WalterAI"
    REDIRECT_URI = "http://localhost:3000/"  # TODO: Fix me!

    client_id: str
    secret: str
    environment: str

    # all the default none fields set during post-int
    configuration: Configuration = None
    api_client: ApiClient = None
    client: PlaidApi = None

    def __post_init__(self) -> None:
        log.debug(
            f"Initializing '{self.environment}' Plaid client with client ID: '{self.client_id}'"
        )
        self.configuration = self._get_configuration()
        self.api_client = ApiClient(self.configuration)
        self.client = PlaidApi(self.api_client)

    def create_link_token(self, user_id: str) -> CreateLinkTokenResponse:
        log.info(f"Creating link token for user '{user_id}'")
        request = LinkTokenCreateRequest(
            products=[Products("auth")],
            client_name=PlaidClient.CLIENT_NAME,
            country_codes=[CountryCode("US")],
            redirect_uri=PlaidClient.REDIRECT_URI,
            language="en",
            webhook="https://webhook.example.com",
            user=LinkTokenCreateRequestUser(client_user_id=user_id),
        )
        response = self.client.link_token_create(request).to_dict()
        return CreateLinkTokenResponse(
            link_token=response["link_token"],
            expiration=response["expiration"],
            request_id=response["request_id"],
            walter_user_id=user_id,
            plaid_user_id=response["user_id"],
        )

    def exchange_public_token(self, public_token: str) -> ExchangePublicTokenResponse:
        log.info("Exchanging Plaid public token for user access token")
        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = self.client.item_public_token_exchange(request)
        access_token = response["access_token"]
        item_id = response["item_id"]
        return ExchangePublicTokenResponse(
            public_token=public_token,
            access_token=access_token,
            item_id=item_id,
        )

    def get_accounts(self, access_token: str) -> None:
        log.info("Getting accounts for user...")
        request = AccountsGetRequest(access_token=access_token)
        accounts_response = self.client.accounts_get(request)
        return accounts_response

    def _get_configuration(self) -> Configuration:
        return Configuration(
            host=self.environment,
            api_key={
                "clientId": self.client_id,
                "secret": self.secret,
            },
        )
