import hashlib
import random
from typing import Optional, override
import loguru

from blockchain.bus import EventBus, EventType
from blockchain.models import AbstractMempoolService
from blockchain.generated.peer_pb2 import Block, Transaction


class MempoolService(AbstractMempoolService):
    def __init__(self, bus: EventBus) -> None:
        self.mempool: dict[bytes, Transaction] = {}
        self.bus = bus

        # Remove committed transactions
        bus.subscribe(EventType.UPDATE, self.update_mempool)

    @override
    def get(self, quantity: Optional[int] = None) -> list[Transaction]:
        if quantity is None or quantity >= len(self.mempool):
            return list(self.mempool.values())
        return random.sample(list(self.mempool.values()), quantity)

    @override
    def get_id(self, tx_id: bytes) -> Optional[Transaction]:
        return self.mempool.get(tx_id, None)

    @override
    def rm(self, tx: Transaction) -> bool:
        txhash = hashlib.sha256(tx.SerializeToString(deterministic=True)).digest()
        return self.rm_id(txhash)

    @override
    def rm_id(self, tx_id: bytes) -> bool:
        if tx_id in self.mempool:
            del self.mempool[tx_id]
            return True
        return False

    @override
    def add(self, tx: Transaction) -> bool:
        txhash = hashlib.sha256(tx.SerializeToString(deterministic=True)).digest()
        if txhash in self.mempool:
            return False

        self.mempool[txhash] = tx
        loguru.logger.debug(f"Transaction {txhash.hex()} added to mempool")
        return True

    async def update_mempool(self, block: Block) -> None:
        for tx in block.body.transactions:
            self.rm(tx)
