import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Optional, Iterable, TypedDict
from .generated import peer_pb2

ValidationFunction = Callable[[Iterable[peer_pb2.UpdateTransaction]], Iterable[bool]]


class AbstractNetworkService(ABC):
    @abstractmethod
    def add_peer(self, peer: str) -> bool:
        pass

    @abstractmethod
    def broadcast_tx(self, tx: peer_pb2.Transaction) -> Awaitable[None]:
        pass

    @abstractmethod
    def broadcast_prevote(self, vote: peer_pb2.PrevoteMessage) -> Awaitable[None]:
        pass

    @abstractmethod
    def broadcast_proposal(self, block: peer_pb2.ProposeBlockRequest) -> Awaitable[None]:
        pass

    @abstractmethod
    def broadcast_precommit(self, precommit: peer_pb2.PrecommitMessage) -> Awaitable[None]:
        pass

    @abstractmethod
    def broadcast_message(self, message: "Message") -> Awaitable[None]:
        pass

    @abstractmethod
    async def get_blockchain(self) -> list[peer_pb2.Block]:
        pass

    @abstractmethod
    def get_peers(self) -> set[str]:
        pass

    @abstractmethod
    async def start(self) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass


@dataclass()
class NetworkConfig(object):
    port: int
    host: str = "localhost"
    peers: set[str] = field(default_factory=set[str])


@dataclass
class NodeConfig(object):
    network: NetworkConfig
    kpriv: Optional[bytes] = None
    validate_fn: Optional[ValidationFunction] = None
    become_validator: bool = False


class LockType(TypedDict):
    round: int
    id: bytes


class ValidType(TypedDict):
    round: int
    id: bytes


class Vote(object):
    def __init__(self, pubkey: bytes, target: bytes):
        """
        :param pubkey: the public key of the validator
        :param target: the hash of the block being voted on.
        If it is a null prevote its going to be binary empty string due to protobuf working like that.
        """
        self.pubkey = pubkey
        self.target = target

    def __hash__(self) -> int:
        return hash(self.pubkey)

    def __eq__(self, value: object) -> bool:
        return isinstance(value, Vote) and self.pubkey == value.pubkey


class Commit(object):
    def __init__(self, pubkey: bytes, target: bytes):
        """
        :param pubkey: the public key of the validator
        :param target: the hash of the block being voted on.
        If it is a null precommit its going to be binary empty string due to protobuf working like that.
        """
        self.pubkey = pubkey
        self.target = target

    def __hash__(self) -> int:
        return hash(self.pubkey)

    def __eq__(self, value: object) -> bool:
        return isinstance(value, Commit) and self.pubkey == value.pubkey


Message = peer_pb2.ProposeBlockRequest | peer_pb2.PrevoteMessage | peer_pb2.PrecommitMessage


class AbstractMessageConsumer(ABC):

    @abstractmethod
    async def receive_proposal(self, message: peer_pb2.ProposeBlockRequest) -> None:
        pass

    @abstractmethod
    async def receive_prevote(self, message: peer_pb2.PrevoteMessage) -> None:
        pass

    @abstractmethod
    async def receive_precommit(self, message: peer_pb2.PrecommitMessage) -> None:
        pass

    @abstractmethod
    async def run(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass


class BaseMessageConsumer(AbstractMessageConsumer):
    def __init__(self, queue: "AbstractMessageService") -> None:
        super().__init__()
        self.loop = asyncio.get_event_loop()
        self.queue = queue

    async def poll_messages(self, get_height: Callable[[], int]) -> None:
        while True:
            message = await self.queue.get(get_height(), timeout=5)
            if not message:
                continue
            if isinstance(message, peer_pb2.ProposeBlockRequest):
                await self.receive_proposal(message)
            elif isinstance(message, peer_pb2.PrevoteMessage):
                await self.receive_prevote(message)
            elif isinstance(message, peer_pb2.PrecommitMessage):
                await self.receive_precommit(message)


class AbstractNode(ABC):
    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def run(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        raise NotImplementedError


class AbstractMempoolService(ABC):
    @abstractmethod
    def get(self, quantity: Optional[int] = None) -> list[peer_pb2.Transaction]:
        raise NotImplementedError

    @abstractmethod
    def get_id(self, tx_id: bytes) -> Optional[peer_pb2.Transaction]:
        raise NotImplementedError

    @abstractmethod
    def rm(self, tx: peer_pb2.Transaction) -> bool:
        raise NotImplementedError

    @abstractmethod
    def rm_id(self, tx_id: bytes) -> bool:
        raise NotImplementedError

    @abstractmethod
    def add(self, tx: peer_pb2.Transaction) -> bool:
        raise NotImplementedError


class AbstractBlockchainService(ABC):
    @abstractmethod
    def update(self, block: peer_pb2.Block) -> None:
        pass

    @property
    @abstractmethod
    def threshold(self) -> int:
        pass

    @property
    @abstractmethod
    def inv_threshold(self) -> int:
        pass

    @property
    @abstractmethod
    def height(self) -> int:
        pass

    @abstractmethod
    def get_last_block(self) -> peer_pb2.Block:
        pass

    @abstractmethod
    def get_last_blocks(self, quantity: Optional[int] = None) -> list[peer_pb2.Block]:
        pass

    @abstractmethod
    def get_balance(self, address: bytes) -> Optional[int]:
        pass

    @abstractmethod
    def get_all_balances(self) -> dict[bytes, int]:
        pass

    @abstractmethod
    def get_validators(self) -> set[bytes]:
        pass

    @abstractmethod
    def is_validator(self, pubkey: bytes) -> bool:
        pass


class AbstractCryptoService(ABC):
    @abstractmethod
    def get_pubkey(self) -> bytes:
        pass

    @abstractmethod
    def sign_proposal(self, round: int, block: peer_pb2.Block) -> peer_pb2.ProposeBlockRequest:
        pass

    @abstractmethod
    def sign_prevote(
        self, height: int, round: int, hash: bytes | None, invalid_txs: Optional[Iterable[bytes]] = None
    ) -> peer_pb2.PrevoteMessage:
        pass

    @abstractmethod
    def sign_precommit(self, height: int, round: int, hash: bytes | None) -> peer_pb2.PrecommitMessage:
        pass

    @abstractmethod
    def sign_transaction(self, tx_data: peer_pb2.TransactionData) -> peer_pb2.Transaction:
        pass

    @abstractmethod
    def verify_message(self, message: Message) -> bool:
        pass

    @abstractmethod
    def verify_transaction(self, tx: peer_pb2.Transaction) -> bool:
        pass


class AbstractValidationService(ABC):
    @abstractmethod
    def validate_tx(self, tx: peer_pb2.Transaction) -> bool:
        pass

    @abstractmethod
    def validate_block(self, block: peer_pb2.Block) -> list[peer_pb2.Transaction]:
        pass


class AbstractMessageService(ABC):
    @abstractmethod
    async def put(self, message: Message) -> None:
        pass

    @abstractmethod
    async def get(self, height: int, timeout: Optional[int] = None) -> Optional[Message]:
        pass

    @abstractmethod
    def empty(self, height: int) -> bool:
        pass
