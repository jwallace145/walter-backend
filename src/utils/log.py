import os
import sys
from dataclasses import dataclass
from logging import FileHandler, Formatter, Handler, Logger, StreamHandler, getLogger

import coloredlogs

LOG_FILE = os.getenv("LOGS_WORKING_DIR", "./") + "logs.log"


@dataclass
class Logger:

    name: str
    log_level: str = os.getenv("LOG_LEVEL", "DEBUG")
    formatter: Formatter = Formatter(
        "%(asctime)s :: %(levelname)s :: %(name)s :: %(message)s"
    )

    def _get_console_handler(self) -> Handler:
        console_handler = StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(self.formatter)
        return console_handler

    def _get_file_handler(self, filename: str) -> Handler:
        file_handler = FileHandler(filename, mode="a+")
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(self.formatter)
        return file_handler

    def get_logger(self) -> Logger:
        logger = getLogger(self.name)
        logger.setLevel(self.log_level)
        logger.addHandler(self._get_console_handler())
        # logger.addHandler(self._get_file_handler(filename=LOG_FILE))
        coloredlogs.install(
            fmt="%(asctime)s :: %(levelname)s :: %(name)s :: %(message)s",
            level=self.log_level,
            logger=logger,
        )
        return logger
