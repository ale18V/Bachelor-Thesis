import asyncio
import random
from typing import Any, Awaitable, Callable, Coroutine, Concatenate, Optional, override
import grpc  # type: ignore
import loguru
from google.protobuf.empty_pb2 import Empty
from google.protobuf.message import Message
from blockchain.constants import GRACE_PERIOD, NUM_CONNECTED_PEERS, PING_TIMEOUT
from blockchain.utils import after_timeout, get_tx_hash_hex
from blockchain.generated import peer_pb2_grpc, peer_pb2
from blockchain.models import AbstractNetworkService, NetworkConfig


class NetworkService(AbstractNetworkService):
    def __init__(self, config: NetworkConfig, loop: asyncio.AbstractEventLoop):
        self.host = config.host
        self.port = config.port
        self.peers: set[str] = config.peers
        self.connections: dict[str, Connection] = {}
        self.loop = loop

        self.logger = loguru.logger

    def with_close(
        self, func: Callable[Concatenate["Connection", ...], Coroutine[Any, Any, None]]
    ) -> Callable[Concatenate["Connection", ...], Coroutine[Any, Any, None]]:

        async def wrapper(connection: Connection, *args: Any, **kwargs: Any) -> None:
            try:
                await func(connection, *args, **kwargs)
            except grpc.RpcError as err:
                self.logger.error(f"Error sending message to {connection.destination}: {err}")
                await self._close_connection(connection.destination)

        return wrapper

    @override
    @loguru.logger.catch
    async def start(self) -> None:
        i = 0
        if not self.peers:
            return

        while len(self.connections) < len(self.peers) < NUM_CONNECTED_PEERS and i < 2 * NUM_CONNECTED_PEERS:
            peer = random.choice(sorted(self.peers))
            await self._run_connection(peer)
            i += 1

    @override
    def add_peer(self, address: str) -> bool:
        # Check if address is self
        # This is not a solution. it works only because I'm running all nodes on the same host
        self.logger.info(f"Add peer request received: {address}")
        if self.is_self_address(address):
            return False

        if not self.peers:
            self.logger.debug(f"First peer connected: {address}")

        if address not in self.peers:
            self.peers.add(address)
            if address not in self.connections:
                self.loop.create_task(self._run_connection(address))
            return True
        return False

    def is_self_address(self, address: str) -> bool:
        """
        Check if address corresponodes to the "origin"
        This is not a solution. It works only when running all nodes on the same host.
        Using grpc sucks because having 2 channels makes it hard to
        associate a pair of outbund and incoming connections to a single entity
        """
        return address.split(":")[1] == str(self.port)

    @loguru.logger.catch
    async def _run_connection(self, address: str) -> None:
        if address in self.connections:
            self.logger.warning(f"Already connected to {address}")
            return

        connection = Connection(address, f"{self.host}:{self.port}")
        new_peers = await connection.run()
        # Deduplicate addresses and remove self
        peers = set(filter(lambda x: not self.is_self_address(x), map(lambda x: x.address, new_peers.addresses)))

        self.peers.update(peers)
        self.connections[address] = connection

    @loguru.logger.catch
    async def _close_connection(self, address: str) -> None:
        if address in self.connections:
            conn = self.connections.pop(address)
            await conn.close()

    async def _broadcast(
        self,
        func: Callable[Concatenate["Connection", Message, ...], Coroutine[Any, Any, None]],
        message: Message,
        log: Optional[str] = None,
    ) -> None:

        async with asyncio.TaskGroup() as tg:
            for connection in self.connections.values():
                tg.create_task(func(connection, message, timeout=5))

        if log:
            self.logger.info(log)

    def broadcast_tx(self, tx: peer_pb2.Transaction) -> Awaitable[None]:
        @self.with_close
        async def send_tx(connection: Connection, tx: peer_pb2.Transaction, *args: Any, **kwargs: Any) -> None:
            await connection.AdvertiseTransaction(tx, *args, **kwargs)

        return self.loop.create_task(self._broadcast(send_tx, tx, f"Broadcasted tx {get_tx_hash_hex(tx)}"))

    def broadcast_proposal(self, request: peer_pb2.ProposeBlockRequest) -> Awaitable[None]:
        @self.with_close
        async def send_block(connection: Connection, request: peer_pb2.ProposeBlockRequest, **kwargs: Any) -> None:
            await connection.ProposeBlock(request, **kwargs)

        return self.loop.create_task(
            self._broadcast(send_block, request, f"Broadcasted block {request.block.header.hash.hex()[:8]}")
        )

    def broadcast_prevote(self, request: peer_pb2.PrevoteMessage) -> Awaitable[None]:
        @self.with_close
        async def send_vote(connection: Connection, request: Any, **kwargs: Any) -> None:
            await connection.AdvertisePrevote(request, **kwargs)

        return self.loop.create_task(
            self._broadcast(
                send_vote, request, f"Broadcasted prevote for {request.hash.hex()[:8] if request.hash else None}"
            )
        )

    def broadcast_precommit(self, request: peer_pb2.PrecommitMessage) -> Awaitable[None]:
        @self.with_close
        async def send_precommit(connection: Connection, request: peer_pb2.PrecommitMessage, **kwargs: Any) -> None:
            await connection.AdvertisePrecommit(request, **kwargs)

        return self.loop.create_task(
            self._broadcast(
                send_precommit, request, f"Broadcasted precommit for {request.hash.hex()[:8] if request.hash else None}"
            )
        )

    @override
    def broadcast_message(self, message: Message) -> Awaitable[None]:
        if isinstance(message, peer_pb2.PrevoteMessage):
            return self.broadcast_prevote(message)
        elif isinstance(message, peer_pb2.PrecommitMessage):
            return self.broadcast_precommit(message)
        elif isinstance(message, peer_pb2.ProposeBlockRequest):
            return self.broadcast_proposal(message)
        else:
            raise ValueError(f"Invalid message type: {type(message)}")

    async def get_blockchain(self) -> list[peer_pb2.Block]:
        if not self.connections:
            raise Exception("No connections available")

        conn = random.choice(list(self.connections.values()))
        resp = await conn.RequestBlockchain(Empty())
        return list(resp.blocks)

    def get_peers(self) -> set[str]:
        return self.peers

    async def stop(self) -> None:
        async with asyncio.TaskGroup() as group:
            for connection in self.connections.values():
                group.create_task(self._close_connection(connection.destination))


class Connection(peer_pb2_grpc.NodeStub):
    def __init__(self, destination: str, origin: str):
        self.channel = grpc.aio.insecure_channel(destination)
        self.origin = origin
        self.destination = destination
        self.logger = loguru.logger
        super().__init__(self.channel)

    async def run(self) -> peer_pb2.RequestPeersResponse:
        self.logger.info(f"Starting connection to {self.destination}")
        res = await self.handshake()
        self.logger.debug(f"Handshake complete with {self.destination}")
        self.keepalive_task = asyncio.get_running_loop().create_task(self.keepalive())
        return res

    async def handshake(self) -> peer_pb2.RequestPeersResponse:
        self.logger.info(f"Starting connection to {self.destination}")
        channel = grpc.aio.insecure_channel(self.destination)
        client = peer_pb2_grpc.NodeStub(channel)
        await client.AdvertisePeer(peer_pb2.NetworkAddress(address=self.origin))
        peers_response: peer_pb2.RequestPeersResponse = await client.RequestPeers(Empty())

        self.logger.info(f"Handshake complete with {self.destination}")

        return peers_response

    @after_timeout(timeout=PING_TIMEOUT)
    async def ping(self) -> bool:
        try:
            self.logger.info(f"Pinging {self.destination}")
            await self.Ping(Empty(), timeout=10)
            self.logger.success(f"Ping successful to {self.destination}")
            return True
        except grpc.RpcError as err:
            self.logger.error(f"GRPC Ping error to {self.destination}: {err}")
            await self.channel.close()
            return False

    async def keepalive(self) -> None:
        while True:
            try:
                res = await self.ping()
                if not res:
                    break
            except Exception as e:
                self.logger.error(f"Connection to {self.destination} lost: {e}")
                break

    async def close(self) -> None:
        self.logger.info(f"Closing connection to {self.destination}")
        if self.keepalive_task:
            self.keepalive_task.cancel()
        await self.channel.close(GRACE_PERIOD)
