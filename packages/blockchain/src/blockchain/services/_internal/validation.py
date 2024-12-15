from typing import Optional, override
from blockchain.generated.peer_pb2 import Block, Transaction
from ...models import AbstractValidationService, ValidationFunction


class ValidationService(AbstractValidationService):
    def __init__(self, validate_fn: Optional[ValidationFunction] = None) -> None:
        self.validate = validate_fn
        pass

    @override
    def validate_block(self, block: Block) -> list[Transaction]:
        if not self.validate:
            return []

        update_txs = list[Transaction](
            filter(lambda tx: tx.data.WhichOneof("body") == "update", block.body.transactions)
        )
        if not update_txs:
            return []
        return list(
            map(
                lambda el: el[0],
                filter(
                    lambda el: bool(el[1]), zip(update_txs, self.validate(map(lambda tx: tx.data.update, update_txs)))
                ),
            )
        )

    @override
    def validate_tx(self, tx: Transaction) -> bool:
        return True
