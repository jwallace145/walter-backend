import json
from dataclasses import dataclass

import yaml

from src.ai.models import WalterModel
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
class UserPortfolioConfig:
    """User Portfolio Configurations"""

    maximum_number_of_stocks: int = 10

    def to_dict(self) -> dict:
        return {
            "maximum_number_of_stocks": self.maximum_number_of_stocks,
        }


@dataclass(frozen=True)
class ArtificialIntelligenceConfig:
    """Artificial Intelligence Configurations"""

    model_name: str = WalterModel.AMAZON_NOVA_MICRO.value
    temperature: float = 0.5
    top_p: float = 0.9

    def to_dict(self) -> dict:
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }


@dataclass(frozen=True)
class NewsSummaryConfig:
    """News Summary Configurations"""

    number_of_articles: int = 10
    lookback_window_days: int = 90
    context: str = "You are an AI investment advisor."
    prompt: str = "Summarize the following '{stock}' news articles:\n{news}"
    max_length: int = 5000
    schedule: str = "cron(0 5 * * ? *)"  # every day at midnight EDT

    def to_dict(self) -> dict:
        return {
            "number_of_articles": self.number_of_articles,
            "lookback_window_days": self.lookback_window_days,
            "context": self.context,
            "prompt": self.prompt,
            "max_length": self.max_length,
            "schedule": self.schedule,
        }


@dataclass(frozen=True)
class NewsletterConfig:
    """Newsletter Configurations"""

    template: str = "default"
    schedule: str = "cron(0 11 ? * MON-FRI *)"  # every business day at 6am EDT

    def to_dict(self) -> dict:
        return {
            "template": self.template,
            "schedule": self.schedule,
        }


@dataclass(frozen=True)
class WalterConfig:
    """
    WalterConfig

    This object maintains the immutable configs of Walter defined in the YAML
    config file.
    """

    user_portfolio: UserPortfolioConfig = UserPortfolioConfig()
    artificial_intelligence: ArtificialIntelligenceConfig = (
        ArtificialIntelligenceConfig()
    )
    news_summary: NewsSummaryConfig = NewsSummaryConfig()
    newsletter: NewsletterConfig = NewsletterConfig()

    def to_dict(self) -> dict:
        return {
            "walter_config": {
                "user_portfolio": self.user_portfolio.to_dict(),
                "artificial_intelligence": self.artificial_intelligence.to_dict(),
                "news_summary": self.news_summary.to_dict(),
                "newsletter": self.newsletter.to_dict(),
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

    config = WalterConfig()  # assume default configs
    try:
        config_yaml = yaml.safe_load(open(CONFIG_FILE).read())["walter_config"]
        config = WalterConfig(
            user_portfolio=UserPortfolioConfig(
                maximum_number_of_stocks=config_yaml["user_portfolio"][
                    "maximum_number_of_stocks"
                ]
            ),
            artificial_intelligence=ArtificialIntelligenceConfig(
                model_name=config_yaml["artificial_intelligence"]["model_name"],
                temperature=config_yaml["artificial_intelligence"]["temperature"],
                top_p=config_yaml["artificial_intelligence"]["top_p"],
            ),
            news_summary=NewsSummaryConfig(
                number_of_articles=config_yaml["news_summary"]["number_of_articles"],
                lookback_window_days=config_yaml["news_summary"][
                    "lookback_window_days"
                ],
                context=config_yaml["news_summary"]["context"],
                prompt=config_yaml["news_summary"]["prompt"],
                max_length=config_yaml["news_summary"]["max_length"],
                schedule=config_yaml["news_summary"]["schedule"],
            ),
            newsletter=NewsletterConfig(
                template=config_yaml["newsletter"]["template"],
                schedule=config_yaml["newsletter"]["schedule"],
            ),
        )
    except Exception as exception:
        log.error(
            "Unexpected error occurred attempting to get configurations!", exception
        )

    log.debug(f"Configurations:\n{json.dumps(config.to_dict(), indent=4)}")

    return config


CONFIG = get_walter_config()
"""(WalterConfig): Config object to be used throughout Walter """
