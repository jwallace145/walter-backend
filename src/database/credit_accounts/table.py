from dataclasses import dataclass

from src.aws.dynamodb.client import WalterDDBClient
from src.database.credit_accounts.models import CreditAccount
from src.environment import Domain
from src.utils.log import Logger

log = Logger(__name__).get_logger()


@dataclass
class CreditAccountsTable:
    """
    WalterDB: CreditAccountsTable
    """

    TABLE_NAME_FORMAT = "CreditAccounts-{domain}"

    ddb: WalterDDBClient
    domain: Domain

    table_name: str = None  # set during post-init

    def __post_init__(self) -> None:
        self.table_name = CreditAccountsTable._get_table_name(self.domain)
        print(f"Initializing CreditAccountsTable with table name '{self.table_name}'")

    def create_account(self, account: CreditAccount) -> CreditAccount:
        log.info(f"Creating a new credit account:\n{account.to_dict()}")
        self.ddb.put_item(self.table_name, account.to_ddb_item())
        return account

    @staticmethod
    def _get_table_name(domain: Domain) -> str:
        return CreditAccountsTable.TABLE_NAME_FORMAT.format(domain=domain.value)
