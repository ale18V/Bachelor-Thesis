import hashlib
import time
from typing import Awaitable, Optional
import loguru

from ...constants import CONSTANT_REWARD_QUANTITY
from ...generated.peer_pb2 import (
    Block,
    BlockBody,
    BlockHeader,
    CoinbaseTransaction,
    Reward,
    StakeTransaction,
    TransactionData,
    UpdateTransaction,
)
from ...models import (
    AbstractBlockchainService,
    AbstractCryptoService,
    AbstractMempoolService,
    AbstractNetworkService,
    AbstractValidationService,
)


class NodeService(object):
    def __init__(
        self,
        blockchain: AbstractBlockchainService,
        mempool: AbstractMempoolService,
        crypto: AbstractCryptoService,
        network: AbstractNetworkService,
        validation: AbstractValidationService,
    ):
        self.blockchain = blockchain
        self.mempool = mempool
        self.crypto = crypto
        self.network = network
        self.validation = validation
        self.logger = loguru.logger

    def is_validator(self) -> bool:
        pk = self.crypto.get_pubkey()
        res = self.blockchain.is_validator(pk)
        self.logger.debug(f"Checking if {pk!r} is a validator: {res}")
        return res

    def craft_block(self, height: int) -> Block:
        transactions = self.mempool.get()
        # for i, tx in enumerate(transactions):
        #     if not self.validation.validate_tx(tx):
        #         self.logger.warning(f"Invalid transaction in mempool: {tx}")
        #         self.mempool.rm(tx)
        #         transactions.pop(i)

        rewards = [
            Reward(address=tx.public_key, quantity=CONSTANT_REWARD_QUANTITY)
            for tx in filter(lambda tx: tx.data.HasField("update"), transactions)
        ]
        if rewards:
            transactions.append(
                self.crypto.sign_transaction(TransactionData(coinbase=CoinbaseTransaction(rewards=rewards)))
            )
        body = BlockBody(transactions=transactions)

        block = Block(
            header=BlockHeader(
                hash=b"",
                valid_round=-1,
                parent=self.blockchain.get_last_block().header.hash,
                timestamp=int(time.time()),
                height=height,
            ),
            body=body,
        )
        hash = hashlib.sha256(block.SerializeToString(deterministic=True)).digest()
        block.header.hash = hash
        return block

    async def sync_blockchain(self) -> bool:
        """Sync the blockchain from a connected peer."""

        try:
            loguru.logger.info("Requesting blockchain from peer...")
            bc = await self.network.get_blockchain()

            # Validate and update local blockchain
            for block in bc[1:]:
                self.blockchain.update(block)

            loguru.logger.debug(f"Blockchain sync complete. Height: {self.blockchain.height}")
            return True
        except Exception as e:
            loguru.logger.error(f"Failed to sync blockchain: {e}")
            return False

    def become_validator(self) -> Awaitable[None]:
        tx = self.crypto.sign_transaction(TransactionData(stake=StakeTransaction(quantity=1000)))
        return self.network.broadcast_tx(tx)

    def broadcast_update(self, data: list[bytes], metadata: Optional[str] = None) -> Awaitable[None]:
        latest_block = self.blockchain.get_last_block().header.hash
        tx = self.crypto.sign_transaction(
            TransactionData(update=UpdateTransaction(block=latest_block, data=data, metadata=metadata))
        )
        return self.network.broadcast_tx(tx)
