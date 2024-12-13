import asyncio
from typing import override
from ...container import Container
from .journal import MessageLog
from ...models import (
    AbstractBlockchainService,
    AbstractMessageService,
    BaseMessageConsumer,
    AbstractNetworkService,
)
from ...generated.peer_pb2 import ProposeBlockRequest, PrecommitMessage, PrevoteMessage
from loguru import logger
from dependency_injector.wiring import Provide, inject

Message = ProposeBlockRequest | PrevoteMessage | PrecommitMessage


class Lightweight(BaseMessageConsumer):
    @logger.catch
    @inject
    def __init__(
        self,
        message_queue: AbstractMessageService = Provide[Container.message_service],
        network_service: AbstractNetworkService = Provide[Container.network_service],
        blockchain_service: AbstractBlockchainService = Provide[Container.blockchain_service],
    ):
        super().__init__(message_queue)
        self.messages = MessageLog()
        self.service = blockchain_service
        self.network = network_service

    @logger.catch
    @override
    async def receive_proposal(self, proposal: ProposeBlockRequest) -> None:
        if not self.messages.add_proposal(proposal):
            logger.debug(f"Proposal already received {proposal.block.header.hash.hex()}")
            return
        await self.network.broadcast_proposal(proposal)

    @logger.catch
    @override
    async def receive_prevote(self, message: PrevoteMessage) -> None:
        if self.messages.add_prevote(message):
            await self.network.broadcast_prevote(message)
            return
        logger.debug(f"Prevote already received {(message.hash or b'').hex()}")

    @logger.catch
    @override
    async def receive_precommit(self, precommit: PrecommitMessage) -> None:
        # Check if the precommit is from a validator
        if not self.service.is_validator(precommit.pubkey):
            logger.error(f"Precommit from non-validator {precommit.pubkey.hex()}")
            return

        if not self.messages.add_precommit(precommit):
            logger.debug(f"Precommit already received {(precommit.hash or b'').hex()}")
            return

        await self.network.broadcast_precommit(precommit)
        # We dont care about null precommits here
        if precommit.hash and self.messages.has_precommit_quorum(
            precommit.round, precommit.hash, self.service.threshold
        ):
            cand = self.messages.get_candidate(precommit.hash)
            if cand:
                logger.success(f"Committing block {cand.header.hash.hex()}")
                self.service.update(cand)
                self.messages.reset()

            else:
                logger.error(f"No candidate for precommit {precommit.hash.hex()} :(")
                # TODO: Should sync here
        else:
            logger.debug(
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
