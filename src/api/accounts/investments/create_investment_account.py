import json
from dataclasses import dataclass
from src.api.common.exceptions import NotAuthenticated, UserDoesNotExist
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import Response, Status, HTTPStatus
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.database.accounts.investment.models import InvestmentAccount
from src.database.client import WalterDB
from src.database.users.models import User
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class CreateInvestmentAccount(WalterAPIMethod):
    """WalterAPI: CreateInvestmentAccount"""

    API_NAME = "CreateInvestmentAccount"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer"}
    REQUIRED_FIELDS = [
        "bank_name",
        "account_name",
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
            CreateInvestmentAccount.API_NAME,
            CreateInvestmentAccount.REQUIRED_QUERY_FIELDS,
            CreateInvestmentAccount.REQUIRED_HEADERS,
            CreateInvestmentAccount.REQUIRED_FIELDS,
            CreateInvestmentAccount.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db

    def execute(self, event: dict, authenticated_email: str) -> Response:
        user = self._verify_user_exists(self.walter_db, authenticated_email)
        investment_account = self._create_new_investment_account(user, event)
        return Response(
            api_name=CreateInvestmentAccount.API_NAME,
            http_status=HTTPStatus.CREATED,
            status=Status.SUCCESS,
            message="Investment account created successfully!",
            data={"investment_account": investment_account.to_dict()},
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True

    def _create_new_investment_account(
        self, user: User, event: dict
    ) -> InvestmentAccount:
        log.info("Creating new investment account for user")

        body = json.loads(event["body"])
        # Create a new investment account with empty portfolios list
        # The create_new_investment_account method doesn't provide all required parameters
        # so we need to modify the returned object
        investment_account = InvestmentAccount.create_new_investment_account(
            user_id=user.user_id,
            bank_name=body["bank_name"],
            account_name=body["account_name"],
            account_last_four_numbers=body["account_last_four_numbers"],
            balance=0.0,  # Default balance to 0.0 as it's not required in the request
        )

        investment_account = self.walter_db.create_investment_account(
            investment_account
        )
        log.info("Investment account created for user successfully!")

        return investment_account
