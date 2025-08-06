import json
from dataclasses import dataclass
from src.api.common.exceptions import NotAuthenticated, UserDoesNotExist
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import Response, Status, HTTPStatus
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.accounts.credit.models import CreditAccount
from src.database.client import WalterDB
from src.database.users.models import User
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class CreateCreditAccount(WalterAPIMethod):
    """WalterAPI: CreateCreditAccount"""

    API_NAME = "CreateCreditAccount"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer"}
    REQUIRED_FIELDS = [
        "bank_name",
        "account_name",
        "balance",
        "account_last_four_numbers",
    ]
    EXCEPTIONS = [
        NotAuthenticated,
        UserDoesNotExist,
    ]

    walter_db: WalterDB

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
    ) -> None:
        super().__init__(
            CreateCreditAccount.API_NAME,
            CreateCreditAccount.REQUIRED_QUERY_FIELDS,
            CreateCreditAccount.REQUIRED_HEADERS,
            CreateCreditAccount.REQUIRED_FIELDS,
            CreateCreditAccount.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str) -> Response:
        user = self._verify_user_exists(self.walter_db, authenticated_email)
        credit_account = self._create_new_credit_account(user, event)
        return Response(
            api_name=CreateCreditAccount.API_NAME,
            http_status=HTTPStatus.CREATED,
            status=Status.SUCCESS,
            message="Credit account created successfully!",
            data={"credit_account": credit_account.to_dict()},
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True

    def _create_new_credit_account(self, user: User, event: dict) -> CreditAccount:
        log.info("Creating new credit account for user")

        body = json.loads(event["body"])
        credit_account = CreditAccount.create_new_credit_account(
            user_id=user.user_id,
            bank_name=body["bank_name"],
            account_name=body["account_name"],
            account_last_four_numbers=body["account_last_four_numbers"],
            balance=float(body["balance"]),
        )

        credit_account = self.walter_db.create_credit_account(credit_account)
        log.info("Credit account created for user successfully!")

        return credit_account
