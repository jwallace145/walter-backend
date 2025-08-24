from dataclasses import dataclass
from typing import Optional

from src.api.common.exceptions import (
    BadRequest,
    NotAuthenticated,
    SessionDoesNotExist,
    UserDoesNotExist,
)
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Response, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.sessions.models import Session
from src.plaid.client import PlaidClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class CreateLinkToken(WalterAPIMethod):
    """
    WalterAPI: CreateLinkToken
    """

    API_NAME = "CreateLinkToken"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer"}
    REQUIRED_FIELDS = []
    EXCEPTIONS = [
        BadRequest,
        NotAuthenticated,
        UserDoesNotExist,
        SessionDoesNotExist,
    ]

    plaid: PlaidClient

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
        plaid: PlaidClient,
    ) -> None:
        super().__init__(
            CreateLinkToken.API_NAME,
            CreateLinkToken.REQUIRED_QUERY_FIELDS,
            CreateLinkToken.REQUIRED_HEADERS,
            CreateLinkToken.REQUIRED_FIELDS,
            CreateLinkToken.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
            walter_db,
        )
        self.plaid = plaid

    def execute(self, event: dict, session: Optional[Session]) -> Response:
        user = self._verify_user_exists(session.user_id)
        response = self.plaid.create_link_token(user.user_id)
        return Response(
            api_name=CreateLinkToken.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Created link token successfully!",
            data=response.to_dict(),
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True
