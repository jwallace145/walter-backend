import json
from dataclasses import dataclass
from typing import Optional

from src.api.common.exceptions import BadRequest, NotAuthenticated, UserDoesNotExist
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Response, Status
from src.auth.authenticator import WalterAuthenticator
from src.database.client import WalterDB
from src.database.sessions.models import Session
from src.database.users.models import User
from src.environment import Domain
from src.metrics.client import DatadogMetricsClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class CreateAccount(WalterAPIMethod):
    """WalterAPI: CreateAccount"""

    API_NAME = "CreateAccount"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer"}
    REQUIRED_FIELDS = [
        "account_type",
        "account_subtype",
        "institution_name",
        "account_name",
        "account_mask",
        "balance",
    ]
    EXCEPTIONS = [
        (BadRequest, HTTPStatus.BAD_REQUEST),
        (NotAuthenticated, HTTPStatus.UNAUTHORIZED),
        (UserDoesNotExist, HTTPStatus.NOT_FOUND),
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
            CreateAccount.API_NAME,
            CreateAccount.REQUIRED_QUERY_FIELDS,
            CreateAccount.REQUIRED_HEADERS,
            CreateAccount.REQUIRED_FIELDS,
            CreateAccount.EXCEPTIONS,
            walter_authenticator,
            metrics,
            walter_db,
        )

    def execute(self, event: dict, session: Optional[Session]) -> Response:
        user = self._verify_user_exists(session.user_id)
        account = self._create_new_account(user, event)
        return Response(
            domain=self.domain,
            api_name=CreateAccount.API_NAME,
            http_status=HTTPStatus.CREATED,
            status=Status.SUCCESS,
            message="Account created successfully!",
            data={"account": account.to_dict()},
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True

    def _create_new_account(self, user: User, event: dict):
        log.info("Creating new account for user")

        body = json.loads(event["body"])
        account = self.db.create_account(
            user_id=user.user_id,
            account_type=body["account_type"],
            account_subtype=body["account_subtype"],
            institution_name=body["institution_name"],
            account_name=body["account_name"],
            account_mask=body["account_mask"],
            balance=float(body["balance"]),
        )

        log.info("Account created for user successfully!")
        return account
