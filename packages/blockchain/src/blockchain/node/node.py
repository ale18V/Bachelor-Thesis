import asyncio
import aiomonitor
import os
from typing import Any, Optional, override
import loguru
from blockchain.models import NodeConfig
from blockchain.constants import GENESIS_BLOCK
from blockchain.consensus import Tendermint, Lightweight
from blockchain.container import Container
from blockchain.bus import EventType
from blockchain.models import (
    AbstractNode,
    Consensus,
)


class Node(AbstractNode):
    logger = loguru.logger

    def __init__(self, config: NodeConfig, container: Optional[Container] = None) -> None:
        if container is None:
            container = Container()
        self.container = container
        self.container.config.from_dict(config.__dict__)
        self.container.init_resources()
        self.container.wire(packages=[__name__, "blockchain.consensus._internal", "blockchain.node"])
        self.server = self.container.server()
        self.network = self.container.network_service()
        self.blockchain = self.container.blockchain_service()
        self.utils = self.container.node_service()
        self.bus = self.container.bus()
        self._stop = asyncio.Event()

    @logger.catch
    @override
    async def start(self) -> None:
        """
        Async version of run. It does not block the main thread and starts the functionalities of the node.
        The coroutine terminates when everything is set up but the node will keep running.
        """
        loop = self.container.loop()
        if os.getenv("DEBUG", False):
            self.monitor = aiomonitor.start_monitor(loop)
            self.monitor.__enter__()

        self.consensus: Consensus
        # Listen to incoming messages
        loop.create_task(self.server.run_async())

        # Open connections to peers
        await self.network.start()
        # Sync the blockchain
        self.blockchain.update(GENESIS_BLOCK)
        await self.utils.sync_blockchain()

        # Instantiate consensus
        if self.utils.is_validator():
            self.consensus = Tendermint()
        else:
            self.consensus = Lightweight()
        loop.create_task(self.consensus.run())

        # Switch the consensus algorithm if the node becomes a validator
        self.unsubscribe = self.bus.subscribe(EventType.UPDATE, self._update_consensus)
        if self.container.config.become_validator():
            await self.utils.become_validator()

    @logger.catch
    @override
    def run(self) -> None:
        """
        Run the node synchronously. This method blocks the main thread and runs until the node is stopped.
        """
        loop = self.container.loop()
        try:
            loop.run_until_complete(self.start())
            loop.run_until_complete(self._stop.wait())
        except KeyboardInterrupt:
            self.logger.info("Node shutting down")
        except Exception as e:
            self.logger.error(f"Node Error: {e}")
        finally:
            if os.getenv("DEBUG", False):
                self.monitor.__exit__(None, None, None)

    @override
    async def stop(self) -> None:
        try:
            await self.server.stop()
            self.consensus.stop()
            await self.network.stop()
            self.unsubscribe()
        except Exception as e:
            self.logger.error(f"Stopping node: {e}")
        finally:
            self._stop.set()

    async def _update_consensus(self, *args: Any) -> None:
        if isinstance(self.consensus, Lightweight) and self.utils.is_validator():
            self.consensus.stop()
            self.consensus = Tendermint()
            await self.consensus.run()
