from typing import Optional

import pytest

from src.api.common.methods import WalterAPIMethod
from src.api.common.models import HTTPStatus, Response, Status
from src.api.factory import APIMethod, APIMethodFactory
from src.api.plaid.create_link_token import CreateLinkToken
from src.api.routing.methods import HTTPMethod
from src.auth.authenticator import WalterAuthenticator
from src.database.client import WalterDB
from src.database.sessions.models import Session
from tst.api.utils import get_api_event


@pytest.fixture
def create_link_token_api(
    api_method_factory: APIMethodFactory,
) -> WalterAPIMethod:
    return api_method_factory.get_api(APIMethod.CREATE_LINK_TOKEN)


def test_create_link_token_success(
    create_link_token_api: CreateLinkToken,
    walter_authenticator: WalterAuthenticator,
    walter_db: WalterDB,
) -> None:
    user_id: str = "user-001"
    session_id: str = "session-001"
    token, expiry = walter_authenticator.generate_access_token(user_id, session_id)
    event: dict = get_api_event(
        path="/plaid/create_link_token", http_method=HTTPMethod.POST, token=token
    )
    session: Optional[Session] = walter_db.get_session(user_id, session_id)
    assert session is not None
    response: Response = create_link_token_api.execute(event, session)
    assert response.api_name == CreateLinkToken.API_NAME
    assert response.http_status == HTTPStatus.OK
    assert response.status == Status.SUCCESS
    assert response.data is not None
    data = response.data
    assert data["request_id"] is not None
    assert data["user_id"] == user_id
    assert data["link_token"] is not None
    assert data["expiration"] is not None
