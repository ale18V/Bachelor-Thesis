from typing import Optional, override
from ...bus import EventBus, EventType
from ...models import AbstractBlockchainService
from ...generated import peer_pb2


class BlockchainService(AbstractBlockchainService):
    def __init__(self, bus: EventBus) -> None:
        self.balances: dict[bytes, int] = {}
        self.validators: set[bytes] = set()
        self.blockchain: list[peer_pb2.Block] = []
        self.bus = bus

    def update(self, block: peer_pb2.Block) -> None:
        # If the block is already in the chain quit

        if any(map(lambda x: x.header.hash == block.header.hash, self.blockchain)):
            return

        self.blockchain.append(block)
        # Reset state
        for tx in block.body.transactions:
            if tx.data.HasField("coinbase"):
                for reward in tx.data.coinbase.rewards:
                    address, quantity = reward.address, reward.quantity
                    if address not in self.balances:
                        self.balances[address] = 0
                    self.balances[address] += quantity

            elif tx.data.HasField("stake"):
                self.validators.add(tx.public_key)

        self.bus.publish(EventType.UPDATE, block)

    @override
    def is_validator(self, pubkey: bytes) -> bool:
        return pubkey in self.validators

    @override
    def get_validators(self) -> set[bytes]:
        return self.validators

    @property
    def threshold(self) -> int:
        validators = len(self.validators)
        return min(validators, int(2 * len(self.validators) / 3) + 1)

    @property
    @override
    def inv_threshold(self) -> int:
        """
        The minimum number of validators that would prevent a majority
        """
        return (len(self.validators) - self.threshold) + 1

    @property
    def height(self) -> int:
        return len(self.blockchain)

    @override
    def get_last_block(self) -> peer_pb2.Block:
        return self.blockchain[-1]

    @override
    def get_last_blocks(self, quantity: Optional[int] = None) -> list[peer_pb2.Block]:
        if not quantity:
            return self.blockchain[:]
        return self.blockchain[-quantity:]

    @override
    def get_balance(self, address: bytes) -> Optional[int]:
        return self.balances.get(address, None)

    @override
    def get_all_balances(self) -> dict[bytes, int]:
        return self.balances.copy()
