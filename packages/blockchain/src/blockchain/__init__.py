import os
import sys
from typing import Literal, Optional
from loguru import logger


_all_ = ["models", "node", "enable_logging"]

logger.disable("blockchain")

Module = Literal["network", "server", "services", "consensus"]


def enable_logging(
    use_custom_fmt: bool = True, path: Optional[str] = None, disable: Optional[list[Module]] = None
) -> None:
    logger.enable("blockchain")

    if use_custom_fmt:
        level = "DEBUG" if os.getenv("DEBUG", False) else "INFO"
        logger.remove(0)
        logger.level("INFO", color="<fg #FFA500>")

        logger.add(
            sink=path if path else sys.stdout,
            format="<level>{time:HH:mm:ss.SSS} {level}</level> <cyan>{file}:{function}:{line}</cyan>: {message}",
            filter=lambda record: record["extra"].get("emitter") != "Tendermint",
            level=level,
        )

        logger.add(
            sink=path if path else sys.stdout,
            level=level,
            colorize=True,
            format=(
                "<level>{time:HH:mm:ss.SSS} {level}</level> <cyan>{function}:{line} {extra[address]} @ {extra[state]} "
                + "H = {extra[height]} R = {extra[round]}</cyan>: {message}"
            ),
            filter=lambda record: record["extra"].get("emitter") == "Tendermint",
        )

    disable = disable or []
    for diasbled_module in disable:
        if diasbled_module == "network":
            diasbled_module = "services._internal.network"  # type: ignore
        logger.disable(f"blockchain.{diasbled_module}")
