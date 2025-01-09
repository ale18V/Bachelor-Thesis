import os
import sys
from loguru import logger


_all_ = ["models", "node"]

logger.remove()
level = "DEBUG" if os.getenv("DEBUG", False) else "INFO"
logger.add(
    sys.stdout,
    format="<level>{time:HH:mm:ss.SSS} {level}</level> <cyan>{name}:{function}:{line}</cyan>: {message}",
    filter=lambda record: record["extra"].get("emitter") != "Tendermint",
    level=level,
)
logger.level("INFO", color="<green>")
