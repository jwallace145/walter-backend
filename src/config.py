import json
from dataclasses import dataclass

import yaml

from src.utils.log import Logger

log = Logger(__name__).get_logger()

CONFIG_FILE = "./config.yml"


@dataclass
class WalterConfig:
    model_id: str = "meta.llama3-70b-instruct-v1:0"
    temperature: float = 0.5
    top_p: float = 0.9
    generate_responses: bool = False
    newsletter_template: str = "default"
    send_newsletter: bool = False
    dump_newsletter: bool = False
    emit_metrics: bool = False
    jwt_algorithm: str = "HS256"

    def __str__(self) -> str:
        return json.dumps(
            {
                "model_id": self.model_id,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "generate_responses": self.generate_responses,
                "newsletter_template": self.newsletter_template,
                "send_newsletter": self.send_newsletter,
                "dump_newsletter": self.dump_newsletter,
                "emit_metrics": self.emit_metrics,
                "jwt_algorithm": self.jwt_algorithm,
            },
            indent=4,
        )


def get_walter_config() -> WalterConfig:
    log.debug(f"Getting configuration file: '{CONFIG_FILE}'")
    try:
        config = yaml.safe_load(open(CONFIG_FILE).read())["walter_config"]
        return WalterConfig(
            model_id=config["model_id"],
            temperature=config["temperature"],
            top_p=config["top_p"],
            generate_responses=config["generate_responses"],
            newsletter_template=config["newsletter_template"],
            send_newsletter=config["send_newsletter"],
            dump_newsletter=config["dump_newsletter"],
            emit_metrics=config["emit_metrics"],
            jwt_algorithm=config["jwt_algorithm"],
        )
    except Exception as exception:
        log.error(
            "Unexpected error occurred attempting to get configuration file!", exception
        )
        return WalterConfig()


CONFIG = get_walter_config()
