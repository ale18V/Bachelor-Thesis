from typing import Callable, Optional, override
from blockchain.generated.peer_pb2 import Block, Transaction, UpdateTransaction
from ...models import AbstractValidationService


class ValidationService(AbstractValidationService):
    def __init__(self, validate_fn: Optional[Callable[[UpdateTransaction], bool]] = None) -> None:
        self.validate = validate_fn
        pass

    @override
    def validate_block(self, block: Block) -> list[Transaction]:
        return list(filter(lambda tx: not self.validate_tx(tx), block.body.transactions))

    @override
    def validate_tx(self, tx: Transaction) -> bool:
        if tx.data.HasField("update") and self.validate:
            return self.validate(tx.data.update)

        return True
