import grpc
from typing import Any
import loguru

from blockchain.constants import GRACE_PERIOD
from .models import (
    AbstractBlockchainService,
    AbstractMempoolService,
    AbstractNetworkService,
    AbstractMessageService,
    NetworkConfig,
)
from .generated.peer_pb2_grpc import NodeServicer
from .generated import peer_pb2
from .generated.peer_pb2 import BalanceResponse, BalanceRequest, ProposeBlockRequest, RequestPeersResponse
from google.protobuf.empty_pb2 import Empty
from .generated import peer_pb2_grpc


class NodeServer(NodeServicer):
    def __init__(
        self,
        config: NetworkConfig,
        network_service: AbstractNetworkService,
        blockchain_service: AbstractBlockchainService,
        mempool_service: AbstractMempoolService,
        message_queue: AbstractMessageService,
    ) -> None:
        super().__init__()
        self.host = config.host
        self.port = config.port
        self.network = network_service
        self.messages = message_queue
        self.service = blockchain_service
        self.mempool = mempool_service
        self.logger = loguru.logger

    @loguru.logger.catch
    async def run_async(self) -> None:
        self.server = grpc.aio.server()
        peer_pb2_grpc.add_NodeServicer_to_server(self, self.server)
        self.server.add_insecure_port(f"{self.host}:{self.port}")
        self.logger.info(f"Starting server on {self.host}:{self.port}")
        await self.server.start()
        self.logger.info("Server started")
        await self.server.wait_for_termination()

    def serve(self) -> None:
        import asyncio

        try:
            asyncio.run(self.run_async())
            asyncio.run(self.server.wait_for_termination())

        except Exception as e:
            self.logger.error(f"Server Error: {e}")
        finally:
            asyncio.run(self.stop())

    async def stop(self) -> None:
        await self.server.stop(GRACE_PERIOD)
        self.logger.info("Server stopped")

    async def Ping(self, _: Any, context: grpc.ServicerContext) -> Empty:
        self.logger.info(f"Pong to {context.peer()}")
        return Empty()

    async def AdvertisePeer(self, request: peer_pb2.NetworkAddress, context: grpc.ServicerContext) -> Empty:
        self.logger.info(f"Received peer: {request.address}. I am {self.host}:{self.port}")
        if request.address == f"{self.host}:{self.port}":
            return Empty()
        self.network.add_peer(request.address)

        return Empty()

    async def RequestPeers(self, request: Empty, context: grpc.ServicerContext) -> RequestPeersResponse:
        return peer_pb2.RequestPeersResponse(
            addresses=([peer_pb2.NetworkAddress(address=x) for x in self.network.get_peers()])
        )

    async def AdvertiseTransaction(self, request: peer_pb2.Transaction, context: grpc.ServicerContext) -> Empty:
        self.logger.debug(f"Received transaction: {request}")

        not_dup = self.mempool.add(request)
        if not_dup:
            self.network.broadcast_tx(request)

        return Empty()

    async def RequestBlock(
        self, request: peer_pb2.BlockRequest, context: grpc.ServicerContext
    ) -> peer_pb2.BlockResponse:
        for block in self.service.get_last_blocks(100):
            if block.header.hash == request.hash:
                return peer_pb2.BlockResponse(block=block)

        return peer_pb2.BlockResponse()

    async def RequestBlockchain(self, _: Any, context: grpc.ServicerContext) -> peer_pb2.BlockchainMessage:
        return peer_pb2.BlockchainMessage(blocks=self.service.get_last_blocks())

    async def RequestBalance(self, request: BalanceRequest, context: grpc.ServicerContext) -> BalanceResponse:
        if request.HasField("address"):
            if balance := self.service.get_balance(request.address):
                return peer_pb2.BalanceResponse(balance=balance)

            return peer_pb2.BalanceResponse()
        else:
            return peer_pb2.BalanceResponse(balance=sum(self.service.get_all_balances().values()))

    async def ProposeBlock(self, request: ProposeBlockRequest, context: grpc.ServicerContext) -> Empty:
        self.logger.debug(f"Received block: {request.block.header.hash.hex()}")
        await self.messages.put(request)

        return Empty()

    async def AdvertisePrevote(self, request: peer_pb2.PrevoteMessage, context: grpc.ServicerContext) -> Empty:
        await self.messages.put(request)
        return Empty()

    async def AdvertisePrecommit(self, request: peer_pb2.PrecommitMessage, context: grpc.ServicerContext) -> Empty:
        await self.messages.put(request)
        return Empty()
