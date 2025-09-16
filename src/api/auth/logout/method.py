import datetime as dt
import time
from dataclasses import dataclass
from typing import Optional

from src.api.common.exceptions import (
    BadRequest,
    NotAuthenticated,
    SessionDoesNotExist,
)
from src.api.common.methods import HTTPStatus, Status, WalterAPIMethod
from src.api.common.models import Response
from src.auth.authenticator import WalterAuthenticator
from src.database.client import WalterDB
from src.database.sessions.models import Session
from src.environment import Domain
from src.metrics.client import DatadogMetricsClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass(kw_only=True)
class Logout(WalterAPIMethod):
    """
    WalterAPI: Logout

    Authenticated API that revokes the current session so that associated
    access and refresh tokens are no longer valid.
    """

    SESSION_HISTORY_TTL_SECONDS = 60 * 60 * 24 * 7  # one week

    API_NAME = "Logout"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"authorization": "Bearer"}
    REQUIRED_FIELDS = []
    EXCEPTIONS = [
        (BadRequest, HTTPStatus.BAD_REQUEST),
        (NotAuthenticated, HTTPStatus.UNAUTHORIZED),
        (SessionDoesNotExist, HTTPStatus.NOT_FOUND),
    ]

    def __init__(
        self,
        domain: Domain,
        walter_authenticator: WalterAuthenticator,
        metrics: DatadogMetricsClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            domain,
            Logout.API_NAME,
            Logout.REQUIRED_QUERY_FIELDS,
            Logout.REQUIRED_HEADERS,
            Logout.REQUIRED_FIELDS,
            Logout.EXCEPTIONS,
            walter_authenticator,
            metrics,
            walter_db,
        )

    def is_authenticated_api(self) -> bool:
        # Requires a valid access token
        return True

    def validate_fields(self, event: dict) -> None:
        # No body fields required
        pass

    def execute(self, event: dict, session: Optional[Session]) -> Response:
        # Extract access token and decode to obtain user_id and token_id (jti)
        access_token = self.authenticator.get_bearer_token(event)
        if access_token is None:
            raise NotAuthenticated("Not authenticated! Token is null.")

        decoded = self.authenticator.decode_access_token(access_token)
        if decoded is None:
            raise NotAuthenticated("Not authenticated! Token is expired or invalid.")

        user_id, token_id = decoded

        # Fetch session and ensure it exists
        session = self.db.get_session(user_id, token_id)
        if session is None:
            raise SessionDoesNotExist("Session does not exist!")

        # Revoke the session and stamp end time
        now = dt.datetime.now(dt.UTC)
        if not session.revoked:
            session.revoked = True
        session.session_end = now
        session.ttl = int(time.time()) + Logout.SESSION_HISTORY_TTL_SECONDS
        self.db.update_session(session)

        log.info(
            f"Revoked session for user '{user_id}' and token ID '{token_id}'. Logout successful."
        )

        return self._create_response(
            HTTPStatus.OK,
            Status.SUCCESS,
            "User logged out successfully!",
            data={
                "user_id": user_id,
                "session_id": token_id,
                "session_start": session.session_start.isoformat(),
                "session_end": session.session_end.isoformat(),
            },
        )
