import asyncio
from typing import override

from ...container import Container
from .journal import MessageLogImpl
from ...models import (
    AbstractBlockchainService,
    AbstractMessageService,
    BaseMessageConsumer,
    AbstractNetworkService,
    Consensus,
)
from ...generated.peer_pb2 import ProposeBlockRequest, PrecommitMessage, PrevoteMessage
from loguru import logger
from dependency_injector.wiring import Provide, inject

Message = ProposeBlockRequest | PrevoteMessage | PrecommitMessage


class Lightweight(BaseMessageConsumer, Consensus):
    @logger.catch
    @inject
    def __init__(
        self,
        message_queue: AbstractMessageService = Provide[Container.message_service],
        network_service: AbstractNetworkService = Provide[Container.network_service],
        blockchain_service: AbstractBlockchainService = Provide[Container.blockchain_service],
    ):
        super().__init__(message_queue)
        self.messages = MessageLogImpl(blockchain_service.threshold)
        self.service = blockchain_service
        self.network = network_service

    @logger.catch
    @override
    async def receive_proposal(self, proposal: ProposeBlockRequest) -> None:
        if not self.messages.add_proposal(proposal):
            logger.warning(f"Proposal already received {proposal.block.header.hash.hex()}")
            return
        await self.network.broadcast_proposal(proposal)

    @logger.catch
    @override
    async def receive_prevote(self, message: PrevoteMessage) -> None:
        if self.messages.add_prevote(message):
            await self.network.broadcast_prevote(message)
            return
        logger.warning(f"Prevote already received {(message.hash or b'').hex()}")

    @logger.catch
    @override
    async def receive_precommit(self, precommit: PrecommitMessage) -> None:
        # Check if the precommit is from a validator
        # if not self.service.is_validator(precommit.pubkey):
        #    raise ValueError("Invalid validator")

        if not self.messages.add_precommit(precommit):
            logger.warning(f"Precommit already received {(precommit.hash or b'').hex()}")
            return

        await self.network.broadcast_precommit(precommit)
        # We dont care about null precommits here
        if not precommit.hash:
            return

        if self.messages.has_precommit_quorum(precommit.round, precommit.hash):
            cand = self.messages.get_candidate(precommit.hash)
            if cand:
                logger.success(f"Committing block {cand.header.hash.hex()}")
                self.service.update(cand)
                self.messages = MessageLogImpl(self.service.threshold)

            else:
                logger.error(f"No candidate for precommit {precommit.hash.hex()} :(")
                # TODO: Should sync here
        else:
            logger.warning(
                f"No precommit quorum for {precommit.hash.hex()} {
                    self.messages.count_precommits_for(precommit.round, precommit.hash)
                    }"
            )

    @override
    async def run(self) -> None:
        self.poll = self.loop.create_task(self.poll_messages(lambda: self.service.height))
        try:
            await self.poll
        except asyncio.CancelledError:
            self.stop()

    @override
    def stop(self) -> None:
        self.poll.cancel()
        logger.info("Consensus stopped")
