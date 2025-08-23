import datetime as dt
from dataclasses import dataclass
from typing import Optional, Tuple

from src.api.auth.refresh.models import RefreshResponseData
from src.api.common.exceptions import (
    BadRequest,
    NotAuthenticated,
    SessionDoesNotExist,
    SessionExpired,
    SessionRevoked,
)
from src.api.common.methods import HTTPStatus, Status, WalterAPIMethod
from src.api.common.models import Response
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.client import WalterDB
from src.database.sessions.models import Session
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class Refresh(WalterAPIMethod):
    """
    WalterAPI: Refresh

    Accepts a refresh token via Authorization Bearer header, validates the corresponding
    session, and issues a new access token using the same JTI as the refresh token.
    """

    API_NAME = "Refresh"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"authorization": "Bearer "}
    REQUIRED_FIELDS = []
    EXCEPTIONS = [
        BadRequest,
        NotAuthenticated,
        SessionDoesNotExist,
        SessionRevoked,
        SessionExpired,
    ]

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            Refresh.API_NAME,
            Refresh.REQUIRED_QUERY_FIELDS,
            Refresh.REQUIRED_HEADERS,
            Refresh.REQUIRED_FIELDS,
            Refresh.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
            walter_db,
        )

    def is_authenticated_api(self) -> bool:
        # This API authenticates using a refresh token rather than the standard access token.
        return False

    def validate_fields(self, event: dict) -> None:
        # No body fields required for this API; header validation handled by base class.
        pass

    def execute(self, event: dict, session: Optional[Session]) -> Response:
        refresh_token = self._get_refresh_token(event)
        user_id, token_id = self._decode_refresh_token(refresh_token)
        session = self._verify_session_exists(user_id, token_id)
        self._verify_valid_session(session)
        access_token, access_token_expiry = self._generate_new_access_token(session)
        return Response(
            api_name=Refresh.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Access token refreshed!",
            data=RefreshResponseData(access_token, access_token_expiry).to_dict(),
        )

    def _get_refresh_token(self, event: dict) -> str:
        log.info("Getting refresh token from event...")
        refresh_token = self.authenticator.get_bearer_token(event)
        if refresh_token is None:
            log.error("Refresh token not found in event!")
            raise NotAuthenticated("Not authenticated! Refresh token is null.")
        log.info("Successfully retrieved refresh token!")
        return refresh_token

    def _decode_refresh_token(self, refresh_token: str) -> Tuple[str, str]:
        log.info("Decoding refresh token...")
        decoded = self.authenticator.decode_refresh_token(refresh_token)
        if decoded is None:
            log.error("Refresh token is invalid or expired!")
            raise NotAuthenticated(
                "Not authenticated! Refresh token is invalid or expired."
            )
        user_id, token_id = decoded
        log.info(
            f"Successfully decoded refresh token for user '{user_id}' and token ID '{token_id}'!"
        )
        return user_id, token_id

    def _verify_session_exists(self, user_id: str, token_id: str) -> Session:
        log.info(
            f"Verifying session exists for user '{user_id}' and token ID '{token_id}'..."
        )
        session = self.db.get_session(user_id, token_id)
        if session is None:
            log.error(
                f"Session for user '{user_id}' and token ID '{token_id}' does not exist!"
            )
            raise SessionDoesNotExist("Session does not exist!")
        log.info(
            f"Successfully verified session exists for user '{user_id}' and token ID '{token_id}'!"
        )
        return session

    def _verify_valid_session(self, session: Session) -> None:
        now = dt.datetime.now(dt.UTC)
        if session.session_expiration < now:
            log.error("Session has expired!")
            raise SessionExpired("Session has expired!")
        if session.revoked:
            log.error("Session has been revoked!")
            raise SessionRevoked("Session has been revoked!")

    def _generate_new_access_token(self, session: Session) -> Tuple[str, dt.datetime]:
        log.info(
            f"Generating new access token for user '{session.user_id}' and token ID '{session.token_id}'"
        )
        new_access_token, new_access_token_expiry = (
            self.authenticator.generate_access_token(session.user_id, session.token_id)
        )
        log.info(
            f"Successfully generated new access token for user '{session.user_id}' and token ID '{session.token_id}'!"
        )
        return new_access_token, new_access_token_expiry
