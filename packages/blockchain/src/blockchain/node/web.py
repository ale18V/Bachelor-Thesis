import asyncio
import signal
from typing import Any, Optional
from loguru import logger
from quart import Quart, Response, jsonify
from hypercorn.asyncio import serve
from hypercorn.config import Config
from google.protobuf.json_format import MessageToDict

from ..models import AbstractBlockchainService, AbstractNetworkService


class WebGui(object):
    def __init__(
        self,
        blockchain_service: AbstractBlockchainService,
        network_service: AbstractNetworkService,
        port: int = 5000,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        self.app = Quart(__name__)
        self.loop = loop or asyncio.get_event_loop()
        self.port = port
        self.blockchain_service = blockchain_service
        self.network_service = network_service

    @logger.catch
    def run(self) -> None:
        """Runs the Quart app as a Hypercorn ASGI server."""
        config = Config()
        config.bind = [f"127.0.0.1:{self.port}"]  # Specify the host and port

        shutdown_event = asyncio.Event()

        @logger.catch
        def shutdown(*args: Any, **kwargs: Any) -> None:
            shutdown_event.set()
            self.loop.stop()
            self.loop.add_signal_handler(signal.SIGINT, shutdown)

        self.loop.create_task(logger.catch(serve)(self.app, config, mode="asgi", shutdown_trigger=shutdown_event.wait))
        self.register_routes()

    def register_routes(self) -> None:
        # === Flask Routes === #
        @self.app.get("/blockchain")
        def get_blockchain() -> Response:
            """Web UI route to view the blockchain."""
            return jsonify([MessageToDict(block) for block in self.blockchain_service.get_last_blocks()])

        @self.app.get("/peers")
        def get_peers() -> Response:
            """Web UI route to view connected peers."""
            return jsonify(list(self.network_service.get_peers()))
