import asyncio
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from dependency_injector.wiring import Provide, inject
from statemachine import Event, State, StateMachine
from blockchain.server import AbstractMempoolService
from blockchain.services import NodeService
from blockchain.utils import get_tx_hash, get_tx_hash_hex
from ...services._internal.messages import MessageService
from .context import TendermintContext
from .timeout import Timeout, TimeoutManager
from ...constants import ACTION_DELAY, PRECOMMIT_TIMEOUT, PREVOTE_TIMEOUT, PROPOSE_TIMEOUT
from .journal import MessageLog
from .utils import is_valid_round
from ...models import (
    AbstractCryptoService,
    AbstractValidationService,
    AbstractBlockchainService,
    AbstractNetworkService,
)
from ...generated.peer_pb2 import Block, ProposeBlockRequest, PrecommitMessage, PrevoteMessage, Transaction
from loguru import logger
import loguru
from ...container import Container
from blockchain.generated import peer_pb2

Message = ProposeBlockRequest | PrevoteMessage | PrecommitMessage


class Tendermint(StateMachine):
    """
    Tendermint algorithm implementation.
    References the description of the paper https://arxiv.org/pdf/1807.04938.
    There are some (non critical?) discrepancies which need to be fixed.
    """

    IDLE = State(initial=True)
    PROPOSE = State()
    PREVOTE = State()
    PRECOMMIT = State()
    FINAL = State(final=True)

    rule1 = PROPOSE.to(PREVOTE)
    rule2 = PROPOSE.to(PREVOTE)
    rule3 = PREVOTE.to(PRECOMMIT) | PRECOMMIT.to(PRECOMMIT)
    rule4 = PRECOMMIT.to(PROPOSE)
    rule5 = PREVOTE.to(PRECOMMIT)
    rule_timeout_prevote = PREVOTE.to(PREVOTE)
    rule_timeout_precommit = PRECOMMIT.to(PRECOMMIT)

    receive_precommit = Event(rule4 | rule_timeout_precommit)
    receive_prevote = Event(rule3 | rule5 | rule_timeout_prevote)
    receive_proposal = Event(rule1 | rule2)
    timeout_precommit = Event(PRECOMMIT.to(PROPOSE))
    timeout_prevote = Event(PREVOTE.to(PRECOMMIT))
    timeout_propose = Event(PROPOSE.to(PREVOTE))

    next_round = Event(PREVOTE.to(PROPOSE) | PROPOSE.to(PROPOSE) | PRECOMMIT.to(PROPOSE))

    _start = IDLE.to(PROPOSE)
    _stop = PREVOTE.to(FINAL) | PROPOSE.to(FINAL) | PRECOMMIT.to(FINAL) | IDLE.to(FINAL)

    @inject
    def __init__(
        self,
        network_service: AbstractNetworkService = Provide[Container.network_service],
        blockchain_service: AbstractBlockchainService = Provide[Container.blockchain_service],
        mempool: AbstractMempoolService = Provide[Container.mempool_service],
        crypto_service: AbstractCryptoService = Provide[Container.crypto_service],
        node_service: NodeService = Provide[Container.node_service],
        validation_service: AbstractValidationService = Provide[Container.validation_service],
        message_queue: MessageService = Provide[Container.message_service],
        loop: asyncio.AbstractEventLoop = Provide[Container.loop],
    ) -> None:
        super().__init__(allow_event_without_transition=True)
        self.network = network_service
        self.service = blockchain_service
        self.crypto_service = crypto_service
        self.message_queue = message_queue
        self.mempool = mempool
        self.messages = MessageLog()
        self.validation_service = validation_service
        self.node_service = node_service
        self.timeout_manager = TimeoutManager(
            {
                self.PROPOSE.name: Timeout(self.timeout_propose, PROPOSE_TIMEOUT),
                self.PREVOTE.name: Timeout(self.timeout_prevote, PREVOTE_TIMEOUT),
                self.PRECOMMIT.name: Timeout(self.timeout_precommit, PRECOMMIT_TIMEOUT),
            }
        )

        # === MISC === #
        self.logger = loguru.logger.bind(
            emitter="Tendermint", address=self.crypto_service.get_pubkey().hex()[:8]
        ).patch(
            lambda record: record["extra"].update(
                height=getattr(self.context, "height", "N/A"),
                round=getattr(self.context, "round", "N/A"),
                state=self.current_state.value,
            )
        )

        # ignore mypy error
        self.context: TendermintContext = TendermintContext(self.service.height, self.service.get_validators())
        # ==== LOOP ==== #
        self.loop = loop
        self.backlog: dict[int, deque[Message]] = dict()

    # ================== ACTIONS ================== #
    async def poll_messages(self) -> None:
        while True:
            message = await self.message_queue.get(self.service.height, timeout=5)
            if not message:
                continue

            if not self.crypto_service.verify_message(message):
                self.logger.error(f"Invalid signature in message from {message.pubkey.hex()[:8]}")
                continue

            if (round := message.round) > self.context.round:
                self.logger.info(f"Received message from future round {round} - Backlogging")
                if round not in self.backlog:
                    self.backlog[round] = deque()
                self.backlog[round].append(message)
                await self.network.broadcast_message(message)
                if len(self.backlog[round]) >= self.service.inv_threshold:
                    await self.next_round()

                continue

            sender = message.pubkey.hex()[:8]
            if isinstance(message, peer_pb2.ProposeBlockRequest):
                if not self.validate_proposal(message):
                    continue
                self.logger.info(f"Received proposal {message.block.header.hash.hex()[:8]} from {sender}")
                await self.network.broadcast_proposal(message)
                await self.receive_proposal(message)
            elif isinstance(message, peer_pb2.PrevoteMessage):
                if not self.validate_prevote(message):
                    continue
                self.logger.info(
                    f"Received prevote for {message.hash.hex()[:8] if message.hash else None} from {sender}\n"
                )
                self.logger.debug(f"Invalid txs: {"\n".join([itx.hex()[:8] for itx in message.invalid_txs])}")
                await self.network.broadcast_prevote(message)
                await self.receive_prevote(message)
            elif isinstance(message, peer_pb2.PrecommitMessage):
                if not self.validate_precommit(message):
                    continue
                self.logger.info(
                    f"Received precommit for {message.hash.hex()[:8] if message.hash else None} from {sender}"
                )
                await self.network.broadcast_precommit(message)
                await self.receive_precommit(message)

    async def run(self) -> None:
        try:
            self.context = TendermintContext(height=self.service.height, validators=self.service.get_validators())
            self.poll = self.loop.create_task(self.poll_messages())
            await self._start()
            await self.poll
        except asyncio.CancelledError:
            self.logger.info("Consensus Stopped")

    def stop(self) -> None:
        for _state, timeout_dict in self.timeout_manager.scheduled_timeouts.items():
            for timeout in timeout_dict.values():
                timeout.cancel()
        self.poll.cancel()
        self.loop.create_task(self._stop())

    # ================== STATES ================== #
    def on_enter_state(self, state: State, event: Event) -> None:
        self.logger.debug(f"Entering {state.value} because of {event.name}")

    @PRECOMMIT.enter
    def _enter_precommit(self) -> None:
        self.timeout_manager.schedule(self.PRECOMMIT.name, self.context.height, self.context.round)

    @PROPOSE.enter
    async def start_round(self) -> None:
        is_proposer = self.context.proposer == self.crypto_service.get_pubkey()
        self.logger.success(
            "Entering new round - "
            + ("I am the proposer" if is_proposer else f"Proposer is {self.context.proposer.hex()[:8]}")
            + f" - Threshold is {self.service.threshold}"
        )
        invalid_txs = list(self.messages.get_invalid_txs(self.context.round - 1, self.service.inv_threshold))
        if invalid_txs:
            self.logger.warning(f"Removing txs {[tx.hex()[:8] for tx in invalid_txs]}")
            for txhash in invalid_txs:
                if self.mempool.rm_id(txhash):
                    self.logger.debug(f"Removed tx {txhash.hex()[:8]} from mempool")

        if self.context.proposer == self.crypto_service.get_pubkey():
            # If the node is a proposer broadcast the proposed block
            block: Block
            if self.context.height == 1 and self.context.round == 0:
                # Wait other nodes when starting the chain
                try:
                    await self.loop.run_in_executor(
                        ThreadPoolExecutor(max_workers=1), input, "Press ENTER when all nodes have connected"
                    )
                    print("Proceeding")
                except Exception as e:
                    self.logger.info(f"Stopping {e}")
                    self.stop()

            if self.context.valid:
                self.logger.info(f"Proposing latest valid block {(self.context.valid['id']).hex()}")
                block = self.messages.get_candidate(self.context.valid["id"])  # type: ignore

            else:
                valid_txs: list[Transaction] = list(
                    filter(
                        bool,  # type: ignore
                        map(
                            lambda id: self.mempool.get_id(id),
                            self.messages.get_valid_txs(self.context.round - 1, self.service.threshold),
                        ),
                    )
                )
                if valid_txs:
                    self.logger.info("Creating new block from valid txs")
                    block = self.node_service.craft_block(self.context.height, valid_txs)
                else:
                    self.logger.info("Creating new block from mempool")
                    block = self.node_service.craft_block(self.context.height, self.mempool.get())

            req = self.crypto_service.sign_proposal(self.context.round, block)
            # Proposer
            await asyncio.sleep(ACTION_DELAY)
            await self.message_queue.put(req)
        else:
            # if node is not a proposer schedule a timeout and wait
            self.timeout_manager.schedule(self.PROPOSE.name, self.context.height, self.context.round)

        if (backlog := self.backlog.get(self.context.round, None)) is not None:
            while backlog:
                message = backlog.popleft()
                self.logger.debug(f"Processing backlog message {message}")
                await self.message_queue.put(message)

    # ================== ACTION CHECKS ================== #
    def validate_proposal(self, req: ProposeBlockRequest) -> bool:
        if req.pubkey != self.context.proposer:
            self.logger.warning(f"Received invalid proposer {req.pubkey.hex()} != {self.context.proposer.hex()}")
            return False
        elif not self.messages.add_proposal(req):
            self.logger.debug(f"Proposal {req.block.header.hash.hex()} already received")
            return False
        return True

    def validate_prevote(self, req: PrevoteMessage) -> bool:
        if req.pubkey not in self.context.validators:
            logger.warning("Invalid validator")
            return False
        elif not self.messages.add_prevote(req):
            logger.debug(f"Prevote {req.hash.hex()[:8] if req.hash else None} already received")
            return False
        return True

    def validate_precommit(self, req: PrecommitMessage) -> bool:
        if req.pubkey not in self.context.validators:
            logger.warning("Invalid validator")
            return False

        elif not self.messages.add_precommit(req):
            logger.debug(f"Precommit {req.hash.hex()[:8] if req.hash else None} already received")
            return False

        return True

    def before_transition(self, event: Event, source: State, target: State) -> None:
        self.logger.debug(f"Transitioning from {source.name} to {target.name} because of {event.name}")

    # ================== RULES ================== #
    rule1.cond(lambda req, **kwargs: not is_valid_round(req))
    rule2.cond(
        lambda req, machine: is_valid_round(req)
        and machine.messages.has_prevote_quorum(
            req.block.header.valid_round, req.block.header.hash, machine.service.threshold
        )
    )

    @rule5.cond
    @rule3.cond
    def _is_prevote_quorum(self, req: PrevoteMessage) -> bool:
        return self.messages.has_prevote_quorum(req.round, req.hash, self.service.threshold)

    @rule5.cond
    @rule3.unless
    def _is_null_prevote(self, req: PrevoteMessage) -> bool:
        return not bool(req.hash)

    rule4.cond(
        lambda req, machine: machine.messages.has_precommit_quorum(req.round, req.hash, machine.service.threshold)
    )

    rule_timeout_prevote.cond(lambda req, machine: machine.messages.count_prevotes(req.round))
    rule_timeout_precommit.cond(lambda req, machine: machine.messages.count_precommits(req.round))

    # ================== TRANSITIONS ================== #
    @rule1.on
    async def _on_rule1(self, req: ProposeBlockRequest) -> None:
        block_id = req.block.header.hash
        target: Optional[bytes] = block_id
        invalid_txs = set(map(lambda tx: get_tx_hash(tx), self.validation_service.validate_block(req.block)))
        if invalid_txs:
            self.logger.error(
                f"Block {block_id.hex()} with invalid txs received: {[id.hex()[:8] for id in invalid_txs]}"
            )
            valid_txs = set(self.messages.get_valid_txs(req.round - 1, self.service.threshold))
            invalid_txs = invalid_txs - valid_txs

        if invalid_txs or (self.context.locked and self.context.locked["id"] != target):
            target = None

        prevote = self.crypto_service.sign_prevote(self.context.height, self.context.round, target, invalid_txs)
        await self.message_queue.put(prevote)
        await asyncio.sleep(ACTION_DELAY)

    @rule2.on
    async def _on_rule2(self, req: ProposeBlockRequest) -> None:
        vr = req.block.header.valid_round
        block_id = req.block.header.hash
        target: Optional[bytes] = block_id
        invalid_txs = set(map(lambda tx: get_tx_hash(tx), self.validation_service.validate_block(req.block)))
        if invalid_txs:
            self.logger.error(
                f"Block {block_id.hex()} with invalid txs received: {[id.hex()[:8] for id in invalid_txs]}"
            )
            valid_txs = set(self.messages.get_valid_txs(req.round - 1, self.service.threshold))
            invalid_txs = invalid_txs - valid_txs

        if invalid_txs or (
            self.context.locked and self.context.locked["round"] > vr and self.context.locked["id"] != target
        ):
            target = None

        prevote = self.crypto_service.sign_prevote(self.context.height, self.context.round, target, invalid_txs)
        await self.message_queue.put(prevote)
        await asyncio.sleep(ACTION_DELAY)

    @rule3.on
    async def _on_rule3(self, req: PrevoteMessage) -> None:
        round, hash = req.round, req.hash

        if self.current_state == self.PREVOTE:
            self.context.lock(round, hash)
            precommit = self.crypto_service.sign_precommit(self.context.height, self.context.round, hash)
            await self.message_queue.put(precommit)

        self.logger.info(f"Received enough prevotes for {hash.hex()}")
        self.context.newvalid(round, hash)

    @rule5.on
    async def _on_rule5(self, req: PrevoteMessage) -> None:
        null_precommit = self.crypto_service.sign_precommit(self.context.height, self.context.round, None)
        await self.message_queue.put(null_precommit)

    @rule4.on
    async def _on_rule4(self, req: PrecommitMessage) -> None:
        if not req.hash:
            self.context.new_round()
            return

        block = self.messages.get_candidate(req.hash)
        if not block:
            self.logger.error(f"No candidate for precommit {req.hash.hex()} :(")
            return
        self.logger.success(f"Block {req.hash.hex()} has been committed\n\n")
        self.service.update(block)
        del self.context
        self.context = TendermintContext(height=self.service.height, validators=self.service.get_validators())
        self.messages.reset()

    @rule_timeout_precommit.on
    @rule_timeout_prevote.on
    def _schedule_timeout(self, req: PrevoteMessage | PrecommitMessage) -> None:
        if isinstance(req, PrevoteMessage):
            self.timeout_manager.schedule(self.PREVOTE.name, req.height, req.round)
        elif isinstance(req, PrecommitMessage):
            self.timeout_manager.schedule(self.PRECOMMIT.name, req.height, req.round)

    # ================== TIMEOUTS ================== #
    @timeout_propose.unless
    @timeout_prevote.unless
    @timeout_precommit.unless
    def timeout_not_relevant(self, height: int, round: int) -> bool:
        return self.context.round != round or self.context.height != height

    @timeout_propose.on
    async def _on_timeout_propose(self, height: int, round: int) -> None:
        req = self.crypto_service.sign_prevote(height, round, None)
        await self.message_queue.put(req)
        self.logger.info("Propose timeout. Casting null vote")

    @timeout_prevote.on
    async def _on_timeout_prevote(self, height: int, round: int) -> None:
        req = self.crypto_service.sign_precommit(height, round, None)
        await self.message_queue.put(req)
        self.logger.info("Prevote timeout. Casting null precommit")

    @timeout_precommit.on
    async def on_timeout_precommit(self, height: int, round: int) -> None:
        self.logger.info("Precommit timeout. Starting new round")
        self.context.new_round()

    @next_round.on
    def _on_next_round(self) -> None:
        self.logger.info("Received enough messages to proceed to next round")
        self.context.new_round()
