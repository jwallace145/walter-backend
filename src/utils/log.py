import logging
import os
from dataclasses import dataclass

import coloredlogs


@dataclass
class Logger:

    name: str
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    enable_colored_logs: bool = os.getenv("ENABLE_COLORED_LOGS", "False") == "True"

    def get_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.name)
        logger.setLevel(self.log_level)
        if self.enable_colored_logs:
            coloredlogs.install(
                level=self.log_level,
                logger=logger,
            )
        return logger
