from src.database.client import WalterDB
from src.database.securities.models import SecurityType
from src.investments.securities.updater import SecurityUpdater


def test_add_security_to_db(
    security_updater: SecurityUpdater, walter_db: WalterDB
) -> None:
    security_ticker = "NFLX"

    # assert security does not exist in db
    assert walter_db.get_security_by_ticker(security_ticker) is None

    # add security to db
    security = security_updater.add_security_if_not_exists(
        security_ticker, SecurityType.STOCK
    )

    # assert security details
    assert security is not None
    assert security.security_id == "sec-nasdaq-nflx"
    assert security.security_type == SecurityType.STOCK

    # assert security exists in db
    assert walter_db.get_security_by_ticker(security_ticker) is not None
