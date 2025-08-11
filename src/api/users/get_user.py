import datetime as dt
from dataclasses import dataclass

from src.api.common.exceptions import UserDoesNotExist, NotAuthenticated
from src.api.common.methods import HTTPStatus, Status
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import Response
from src.auth.authenticator import WalterAuthenticator
from src.aws.cloudwatch.client import WalterCloudWatchClient
from src.aws.s3.client import WalterS3Client
from src.aws.secretsmanager.client import WalterSecretsManagerClient
from src.database.client import WalterDB

from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class GetUser(WalterAPIMethod):
    """
    WalterAPI - GetUser

    This API gets the user from their identity token. Walter
    uses JSON web tokens to authenticate users and this method
    is responsible for validating identity tokens and returning
    user information. This API method is used by the frontend
    to display all user information.
    """

    DATE_FORMAT = "%Y-%m-%d"

    API_NAME = "GetUser"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer"}
    REQUIRED_FIELDS = []
    EXCEPTIONS = [NotAuthenticated, UserDoesNotExist]

    walter_db: WalterDB
    walter_sm: WalterSecretsManagerClient
    walter_s3: WalterS3Client

    def __init__(
        self,
        walter_authenticator: WalterAuthenticator,
        walter_cw: WalterCloudWatchClient,
        walter_db: WalterDB,
        walter_sm: WalterSecretsManagerClient,
        walter_s3: WalterS3Client,
    ) -> None:
        super().__init__(
            GetUser.API_NAME,
            GetUser.REQUIRED_QUERY_FIELDS,
            GetUser.REQUIRED_HEADERS,
            GetUser.REQUIRED_FIELDS,
            GetUser.EXCEPTIONS,
            walter_authenticator,
            walter_cw,
        )
        self.walter_db = walter_db
        self.walter_sm = walter_sm
        self.walter_s3 = walter_s3

    def execute(self, event: dict, authenticated_email: str) -> Response:
        user = self.walter_db.get_user(authenticated_email)
        if user is None:
            raise UserDoesNotExist("User does not exist!")

        # update user last active date
        user.last_active_date = dt.datetime.now(dt.UTC)

        # update user profile picture url if it has expired
        now = dt.datetime.now(dt.UTC)
        if user.profile_picture_s3_uri and now > user.profile_picture_url_expiration:
            log.info(
                "User custom profile picture presigned URL has expired! Generating new one now..."
            )
            bucket, key = WalterS3Client.get_bucket_and_key(user.profile_picture_s3_uri)
            user.profile_picture_url, user.profile_picture_url_expiration = (
                self.walter_s3.create_presigned_get_object_url(
                    bucket=bucket,
                    key=key,
                    expiration_in_seconds=3600,
                )
            )

        # save user and any updates to db
        self.walter_db.update_user(user)

        return Response(
            api_name=GetUser.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Successfully retrieved user!",
            data={
                "email": authenticated_email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "verified": user.verified,
                "subscribed": user.subscribed,
                "sign_up_date": user.sign_up_date.strftime(GetUser.DATE_FORMAT),
                "last_active_date": user.last_active_date.strftime(GetUser.DATE_FORMAT),
                "profile_picture_url": user.profile_picture_url,
                "free_trial_end_date": user.free_trial_end_date.strftime(
                    GetUser.DATE_FORMAT
                ),
                "active_stripe_subscription": (
                    True if user.stripe_subscription_id else False
                ),
            },
        )

    def validate_fields(self, event: dict) -> None:
        pass  # no payload for get user requests

    def is_authenticated_api(self) -> bool:
        return True
