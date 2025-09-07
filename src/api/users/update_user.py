import base64
import datetime as dt
from dataclasses import dataclass

from requests_toolbelt.multipart import decoder

from src.api.common.exceptions import BadRequest, NotAuthenticated, UserDoesNotExist
from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Response, Status
from src.auth.authenticator import WalterAuthenticator
from src.aws.s3.client import WalterS3Client
from src.database.client import WalterDB
from src.environment import Domain
from src.metrics.client import DatadogMetricsClient
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class UpdateUser(WalterAPIMethod):
    """
    WalterAPI: UpdateUser
    """

    API_NAME = "UpdateUser"
    REQUIRED_QUERY_FIELDS = []
    REQUIRED_HEADERS = {"Authorization": "Bearer"}
    REQUIRED_FIELDS = []
    EXCEPTIONS = [
        (NotAuthenticated, HTTPStatus.UNAUTHORIZED),
        (UserDoesNotExist, HTTPStatus.NOT_FOUND),
    ]

    walter_s3: WalterS3Client

    def __init__(
        self,
        domain: Domain,
        walter_authenticator: WalterAuthenticator,
        metrics: DatadogMetricsClient,
        walter_db: WalterDB,
        walter_s3: WalterS3Client,
    ) -> None:
        super().__init__(
            domain,
            UpdateUser.API_NAME,
            UpdateUser.REQUIRED_QUERY_FIELDS,
            UpdateUser.REQUIRED_HEADERS,
            UpdateUser.REQUIRED_FIELDS,
            UpdateUser.EXCEPTIONS,
            walter_authenticator,
            metrics,
            walter_db,
        )
        self.walter_s3 = walter_s3

    def execute(self, event: dict, authenticated_email: str) -> Response:
        user = self.db.get_user(authenticated_email)
        if user is None:
            raise UserDoesNotExist("User does not exist!")

        body = base64.b64decode(event["body"])
        content_type = event["headers"].get("Content-Type") or event["headers"].get(
            "content-type"
        )

        multipart_data = decoder.MultipartDecoder(body, content_type)

        # set image file
        image_file = None
        for part in multipart_data.parts:
            content_disposition = part.headers[b"Content-Disposition"].decode()
            if 'name="profile_picture"' in content_disposition:
                image_file = part.content

        # ensure image file was set
        if not image_file:
            raise BadRequest("Missing image file!")

        bucket = "walterai-media-dev"
        key = f"profile-pictures/{user.user_id}.jpeg"
        s3_uri = WalterS3Client.get_uri(bucket, key)
        self.walter_s3.put_object(
            bucket=bucket,
            key=key,
            contents=image_file,
            content_type="image/jpeg",
        )

        # update profile picture and set expiration date to force
        # profile picture url refresh on next GetUser API call
        user.profile_picture_s3_uri = s3_uri
        user.profile_picture_url_expiration = dt.datetime.now(dt.UTC)

        self.db.update_user(user)

        return Response(
            domain=self.domain,
            api_name=UpdateUser.API_NAME,
            http_status=HTTPStatus.OK,
            status=Status.SUCCESS,
            message="Updated user!",
        )

    def validate_fields(self, event: dict) -> None:
        pass

    def is_authenticated_api(self) -> bool:
        return True
