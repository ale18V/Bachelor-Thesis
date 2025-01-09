import asyncio
from enum import Enum
from inspect import isawaitable
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Concatenate, Coroutine, Optional, ParamSpec, TypeVar, override
from dependency_injector.wiring import Provide, inject
from blockchain.services import NodeService
from ...services._internal.messages import MessageService
from .context import TendermintContext
from .timeout import Timeout, TimeoutFactory
from ...constants import ACTION_DELAY, PRECOMMIT_TIMEOUT, PREVOTE_TIMEOUT, PROPOSE_TIMEOUT
from .journal import MessageLogImpl
from .utils import is_valid_round
from ...models import (
    AbstractCryptoService,
    AbstractValidationService,
    BaseMessageConsumer,
    AbstractBlockchainService,
    Consensus,
    MessageLog,
    AbstractNetworkService,
)
from ...generated.peer_pb2 import Block, ProposeBlockRequest, PrecommitMessage, PrevoteMessage
from loguru import logger
import loguru
from ...container import Container

Message = ProposeBlockRequest | PrevoteMessage | PrecommitMessage


class State(Enum):
    IDLE = "Idle"
    PROPOSE = "Proposal"
    PREVOTE = "Prevote"
    PRECOMMIT = "Precommit"
    FINAL = "Final"

    def __str__(self) -> str:
        return self.value.upper()


class Tendermint(BaseMessageConsumer, Consensus):
    """
    Tendermint algorithm implementation.
    References the description of the paper https://arxiv.org/pdf/1807.04938.
    There are some (non critical?) discrepancies which need to be fixed.
    """

    @staticmethod
    def _to_state(state: State, conditional: bool = False):  # type: ignore
        P = ParamSpec("P")
        R = TypeVar("R")

        def decorator(
            func: Callable[Concatenate["Tendermint", P], R]
        ) -> Callable[Concatenate["Tendermint", P], Coroutine[Any, Any, R]]:
            async def wrapper(self: "Tendermint", *args: P.args, **kwargs: P.kwargs) -> R:
                res = func(self, *args, **kwargs)
                if isawaitable(res):
                    res = await res

                if conditional and not res:
                    return res

                loguru.logger.info(f"Transitioning to state {state} because of {func.__name__}")
                self.state = state
                return res

            return wrapper

        return decorator

    @inject
    def __init__(
        self,
        network_service: AbstractNetworkService = Provide[Container.network_service],
        blockchain_service: AbstractBlockchainService = Provide[Container.blockchain_service],
        crypto_service: AbstractCryptoService = Provide[Container.crypto_service],
        node_service: NodeService = Provide[Container.node_service],
        validation_service: AbstractValidationService = Provide[Container.validation_service],
        message_queue: MessageService = Provide[Container.message_service],
        loop: asyncio.AbstractEventLoop = Provide[Container.loop],
    ) -> None:
        super().__init__(queue=message_queue)
        self.network = network_service
        self.service = blockchain_service
        self.crypto_service = crypto_service
        self.message_queue = message_queue
        self.messages: MessageLog = MessageLogImpl(threshold=self.service.threshold)
        self.validation_service = validation_service
        self.node_service = node_service
        self.state = State.IDLE
        self.timeout_factory = TimeoutFactory(
            {
                State.PROPOSE.value: Timeout(self.on_timeout_propose, PROPOSE_TIMEOUT),
                State.PREVOTE.value: Timeout(self.on_timeout_prevote, PREVOTE_TIMEOUT),
                State.PRECOMMIT.value: Timeout(
                    self.on_timeout_precommit, PRECOMMIT_TIMEOUT, "Precommit timeout ticked"
                ),
            }
        )

        # === MISC === #
        self.logger = loguru.logger.bind(emitter="Tendermint").patch(
            lambda record: record["extra"].update(
                height=getattr(self.context, "height", "N/A"),
                round=getattr(self.context, "round", "N/A"),
                state=self.state,
            )
        )
        level = "DEBUG" if os.getenv("DEBUG", False) else "INFO"
        logger.add(
            sys.stdout,
            level=level,
            colorize=True,
            format="<level>{time:HH:mm:ss.SSS} {level}</level> <cyan>{name}:{line} @ {extra[state]} "
            + "H = {extra[height]} R = {extra[round]}</cyan>: {message}",
            filter=lambda record: record["extra"].get("emitter") == "Tendermint",
        )

        # ignore mypy error
        self.context: TendermintContext = TendermintContext(self.service.height, self.service.get_validators())
        # ==== LOOP ==== #
        self.loop = loop

    # ================== ACTIONS ================== #
    @override
    async def run(self) -> None:
        if self.state != State.IDLE:
            return
        self.context = TendermintContext(height=self.service.height, validators=self.service.get_validators())
        self.poll = self.loop.create_task(self.poll_messages(lambda: getattr(self.context, "height", 0)))
        self.state = State.PROPOSE
        self.loop.create_task(self.start_round())
        try:
            await self.poll
        except asyncio.CancelledError:
            self.logger.info("Consensus stopped")

    @override
    def stop(self) -> None:
        for _state, timeout_dict in self.timeout_factory.scheduled_timeouts.items():
            for timeout in timeout_dict.values():
                timeout.cancel()
        self.poll.cancel()
        self.state = State.FINAL

    # ================== MESSAGE HANDLERS ================== #
    @override
    async def receive_proposal(self, req: ProposeBlockRequest) -> None:
        if not self.validate_proposal(req):
            return

        self.logger.info(f"Received proposal from {req.pubkey.hex()} for {req.block.header.hash.hex()}")
        if self.rule1_cond(req):
            await self.rule1(req)
        elif self.rule2_cond(req):
            await self.rule2(req)

        await self.network.broadcast_proposal(req)

    def rule2_cond(self, req: ProposeBlockRequest) -> bool:
        return (
            self.state == State.PROPOSE
            and is_valid_round(req)
            and self.messages.has_prevote_quorum(req.block.header.valid_round, req.block.header.hash)
        )

    def rule1_cond(self, req: ProposeBlockRequest) -> bool:
        return self.state == State.PROPOSE and not is_valid_round(req)

    @override
    async def receive_prevote(self, req: PrevoteMessage) -> None:
        if not self.validate_prevote(req):
            return

        self.logger.info(f"Received prevote from {req.pubkey.hex()} for {req.hash.hex()}")
        if self.rule3_cond(req):
            await self.rule3(req)
        elif not self.timeout_factory.is_scheduled(self.state.value, self.context.height, self.context.round):
            self.timeout_factory.schedule(self.state.value, self.context.height, self.context.round)
        await self.network.broadcast_prevote(req)

    def rule3_cond(self, req: PrevoteMessage) -> bool:
        return self.state in (State.PREVOTE, State.PRECOMMIT) and self.messages.has_prevote_quorum(req.round, req.hash)

    @override
    async def receive_precommit(self, req: PrecommitMessage) -> None:
        if not self.validate_precommit(req):
            return

        self.logger.info(f"Received precommit from {req.pubkey.hex()} for {req.hash.hex()}")
        # TODO: Validate? self.service.validate_block(block)
        if self.rule4_cond(req):
            await self.rule4(req)
        elif not self.timeout_factory.is_scheduled(self.state.value, self.context.height, self.context.round):
            self.timeout_factory.schedule(self.state.value, self.context.height, self.context.round)
        await self.network.broadcast_precommit(req)

    def rule4_cond(self, req: PrecommitMessage) -> bool:
        return self.messages.get_candidate(req.hash) is not None and self.messages.has_precommit_quorum(
            req.round, req.hash
        )

    # ================== ACTION CHECKS ================== #
    def validate_proposal(self, req: ProposeBlockRequest) -> bool:
        if req.pubkey != self.context.proposer:
            self.logger.warning(f"Received invalid proposer {req.pubkey.hex()} != {self.context.proposer.hex()}")
        else:
            res = self.messages.add_proposal(req)
            if res:
                return True
            self.logger.debug(f"Proposal {req.block.header.hash.hex()} already received")
        return False

    def validate_prevote(self, req: PrevoteMessage) -> bool:
        if req.pubkey not in self.context.validators:
            logger.warning("Invalid validator")
        else:
            res = self.messages.add_prevote(req)
            if res:
                return True
            logger.debug(f"Prevote {(req.hash or b'').hex()} already received")
        return False

    def validate_precommit(self, req: PrecommitMessage) -> bool:
        if req.pubkey not in self.context.validators:
            logger.warning("Invalid validator")
        else:
            res = self.messages.add_precommit(req)
            if res:
                return True
            logger.debug(f"Precommit {(req.hash or b'').hex()} already received")
        return False

    # ================== STATES ================== #
    async def start_round(self) -> None:
        self.logger.info(
            f"Entering new round - Proposer is {self.context.proposer.hex()} - Threshold is {self.service.threshold}"
        )
        # if node is not a proposer schedule a timeout and wait
        if self.context.proposer != self.crypto_service.get_pubkey():
            self.timeout_factory.schedule(self.state.value, self.context.height, self.context.round)
            return

        # If the node is a proposer broadcast the proposed block
        self.logger.info("I am the proposer")

        block: Block
        if self.context.height == 1 and self.context.round == 0:
            try:
                await self.loop.run_in_executor(ThreadPoolExecutor(max_workers=1), input, "Press enter to proceed")
                print("Proceeding")
            except Exception as e:
                self.logger.info(f"Stopping {e}")
                self.stop()
        if self.context.valid:
            self.logger.info(f"Proposing latest valid block {(self.context.valid['id'] or b'').hex()}")
            block = self.messages.get_candidate(self.context.valid["id"])  # type: ignore

        else:
            self.logger.info("Creating new block from mempool")
            block = self.node_service.craft_block(self.context.height)

        req = self.crypto_service.sign_proposal(self.context.round, block)
        # Proposer
        await asyncio.sleep(ACTION_DELAY)
        await self.message_queue.put(req)

    # ================== TRANSITIONS ================== #
    @_to_state(State.PREVOTE)
    async def rule1(self, req: ProposeBlockRequest) -> None:
        target: Optional[bytes] = req.block.header.hash
        if not self.validation_service.validate_block(req.block) or (
            self.context.locked and self.context.locked["id"] != target
        ):
            target = None

        prevote = self.crypto_service.sign_prevote(self.context.height, self.context.round, target)
        await self.message_queue.put(prevote)
        await asyncio.sleep(ACTION_DELAY)

    @_to_state(State.PREVOTE)
    async def rule2(self, req: ProposeBlockRequest) -> None:
        vr = req.block.header.valid_round
        target: Optional[bytes] = req.block.header.hash
        if not self.validation_service.validate_block(req.block) or (
            self.context.locked and self.context.locked["round"] > vr and self.context.locked["id"] != target
        ):
            target = None

        prevote = self.crypto_service.sign_prevote(self.context.height, self.context.round, target)
        await self.message_queue.put(prevote)
        await asyncio.sleep(ACTION_DELAY)

    @_to_state(State.PRECOMMIT)
    async def rule3(self, req: PrevoteMessage) -> None:
        round, hash = req.round, req.hash

        if self.state == State.PREVOTE:
            self.context.lock(round, hash)
            precommit = self.crypto_service.sign_precommit(self.context.height, self.context.round, hash)
            await self.message_queue.put(precommit)
        self.context.newvalid(round, hash)

    async def rule4(self, req: PrecommitMessage) -> None:
        self.logger.success(f"Block {req.hash.hex()} has been committed\n\n")
        block = self.messages.get_candidate(req.hash)
        if not block:
            self.logger.error(f"No candidate for precommit {req.hash.hex()} :(")
            return
        self.service.update(block)
        del self.context
        self.context = TendermintContext(height=self.service.height, validators=self.service.get_validators())
        self.messages.reset(self.service.threshold)
        self.state = State.PROPOSE
        await self.start_round()

    # ================== TIMEOUTS ================== #
    def timeout_not_relevant(self, height: int, round: int) -> bool:
        return self.context.round != round or self.context.height != height

    @_to_state(State.PREVOTE, conditional=True)
    async def on_timeout_propose(self, height: int, round: int) -> bool:
        if self.timeout_not_relevant(height, round):
            return False
        self.logger.info("Propose timeout. Casting null vote")
        req = self.crypto_service.sign_prevote(height, round, None)
        await self.message_queue.put(req)
        return True

    @_to_state(State.PRECOMMIT, conditional=True)
    async def on_timeout_prevote(self, height: int, round: int) -> bool:
        if self.timeout_not_relevant(height, round):
            return False
        self.logger.info("Prevote timeout. Casting null precommit")
        req = self.crypto_service.sign_precommit(height, round, None)
        await self.message_queue.put(req)
        return True

    async def on_timeout_precommit(self, height: int, round: int) -> None:
        if self.timeout_not_relevant(height, round):
            return
        self.logger.info("Precommit timeout. Starting new round")
        self.context.next_round()
        self.state = State.PROPOSE
        await self.start_round()
