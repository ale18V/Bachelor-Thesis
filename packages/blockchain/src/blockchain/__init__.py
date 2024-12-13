import os
import sys
from loguru import logger


_all_ = ["models", "node", "configure_logging"]

logger.disable("blockchain")


def configure_logging() -> None:
    logger.enable("blockchain")
    logger.remove()
    level = "DEBUG" if os.getenv("DEBUG", False) else "INFO"
    logger.add(
        sys.stdout,
        format="<level>{time:HH:mm:ss.SSS} {level}</level> <cyan>{file}:{function}:{line}</cyan>: {message}",
        filter=lambda record: record["extra"].get("emitter") != "Tendermint",
        level=level,
    )
    logger.level("INFO", color="<green>")
    logger.disable("blockchain.services._internal.network")
    logger.disable("blockchain.server")


configure_logging()
