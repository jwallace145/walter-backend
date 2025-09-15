import pytest

from src.canaries.accounts.get_accounts import GetAccounts
from src.canaries.auth.login import Login
from src.canaries.auth.logout import Logout
from src.canaries.auth.refresh import Refresh
from src.canaries.routing.router import CanaryRouter, CanaryType
from src.canaries.transactions.get_transactions import GetTransactions
from src.canaries.users.create_user import CreateUser
from src.canaries.users.get_user import GetUser


def test_get_canary_success(canary_router: CanaryRouter) -> None:
    assert isinstance(canary_router.get_canary(CanaryType.LOGIN), Login)
    assert isinstance(canary_router.get_canary(CanaryType.REFRESH), Refresh)
    assert isinstance(canary_router.get_canary(CanaryType.LOGOUT), Logout)
    assert isinstance(canary_router.get_canary(CanaryType.GET_USER), GetUser)
    assert isinstance(canary_router.get_canary(CanaryType.CREATE_USER), CreateUser)
    assert isinstance(canary_router.get_canary(CanaryType.GET_ACCOUNTS), GetAccounts)
    assert isinstance(
        canary_router.get_canary(CanaryType.GET_TRANSACTIONS), GetTransactions
    )


def test_get_canary_failure(canary_router: CanaryRouter) -> None:
    with pytest.raises(Exception):
        canary_router.get_canary("invalid-canary")
