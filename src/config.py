import json
from dataclasses import dataclass

import yaml

from src.utils.log import Logger

log = Logger(__name__).get_logger()

#############
# CONSTANTS #
#############

CONFIG_FILE = "./config.yml"
"""(str): The location of the YAML config file."""

##########
# MODELS #
##########


@dataclass(frozen=True)
class ExpenseCategorizationConfig:
    """Expense Categorization Configurations"""

    num_hidden_layers: int = 32

    def to_dict(self) -> dict:
        return {
            "num_hidden_layers": self.num_hidden_layers,
        }


@dataclass(frozen=True)
class AuthConfig:
    """Auth Configurations"""

    access_token_expiration_minutes: int
    refresh_token_expiration_days: int

    def to_dict(self) -> dict:
        return {
            "access_token_expiration_minutes": self.access_token_expiration_minutes,
            "refresh_token_expiration_days": self.refresh_token_expiration_days,
        }


@dataclass(frozen=True)
class CanariesConfig:
    """Canaries Configurations"""

    endpoint: str
    user_id: str
    user_email: str
    user_password: str

    def to_dict(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "user_password": self.user_password,
        }


@dataclass(frozen=True)
class PlaidConfig:
    """Plaid Configurations"""

    client_name: str
    redirect_uri: str
    sync_transactions_webhook_url: str

    def to_dict(self) -> dict:
        return {
            "client_name": self.client_name,
            "redirect_uri": self.redirect_uri,
            "sync_transactions_webhook_url": self.sync_transactions_webhook_url,
        }


@dataclass(frozen=True)
class WalterConfig:
    """
    WalterConfig

    This object maintains the immutable configs of Walter defined in the YAML
    config file.
    """

    expense_categorization: ExpenseCategorizationConfig
    auth: AuthConfig
    canaries: CanariesConfig
    plaid: PlaidConfig = PlaidConfig

    def to_dict(self) -> dict:
        return {
            "walter_config": {
                "expense_categorization": self.expense_categorization.to_dict(),
                "auth": self.auth.to_dict(),
                "canaries": self.canaries.to_dict(),
                "plaid": self.plaid.to_dict(),
            }
        }

    def __str__(self) -> str:
        return json.dumps(self.to_dict(), indent=4)


##########
# CONFIG #
##########


def get_walter_config() -> WalterConfig:
    """
    Get the configurations for Walter from the config YAML file.

    This method reads the given configurations from the specified config YAML file.
    However, if this method encounters an exception for any reason, it returns the
    default configs to ensure this method cannot cause Walter to fail.

    Returns:
        (WalterConfig): The Walter configurations.
    """
    log.debug(f"Getting configuration file: '{CONFIG_FILE}'")

    try:
        config_yaml = yaml.safe_load(open(CONFIG_FILE).read())["walter_config"]
        config = WalterConfig(
            expense_categorization=ExpenseCategorizationConfig(
                num_hidden_layers=config_yaml["expense_categorization"][
                    "num_hidden_layers"
                ]
            ),
            auth=AuthConfig(
                access_token_expiration_minutes=config_yaml["auth"][
                    "access_token_expiration_minutes"
                ],
                refresh_token_expiration_days=config_yaml["auth"][
                    "refresh_token_expiration_days"
                ],
            ),
            canaries=CanariesConfig(
                endpoint=config_yaml["canaries"]["endpoint"],
                user_id=config_yaml["canaries"]["user_id"],
                user_email=config_yaml["canaries"]["user_email"],
                user_password=config_yaml["canaries"]["user_password"],
            ),
            plaid=PlaidConfig(
                client_name=config_yaml["plaid"]["client_name"],
                redirect_uri=config_yaml["plaid"]["redirect_uri"],
                sync_transactions_webhook_url=config_yaml["plaid"][
                    "sync_transactions_webhook_url"
                ],
            ),
        )
    except Exception as exception:
        log.error(
            "Unexpected error occurred attempting to get configurations!", exception
        )
        raise ValueError("Unexpected error occurred attempting to get configurations!")

    log.debug(f"Configurations:\n{json.dumps(config.to_dict(), indent=4)}")

    return config


CONFIG = get_walter_config()
"""(WalterConfig): Config object to be used throughout Walter """
