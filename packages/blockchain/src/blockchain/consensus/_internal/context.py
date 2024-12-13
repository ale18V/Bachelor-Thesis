from typing import Optional
from blockchain.models import LockType, ValidType
from .utils import get_proposer


class TendermintContext:
    height: int
    round: int
    validators: set[bytes]
    locked: Optional[LockType]
    valid: Optional[ValidType]
    proposer: bytes

    def __init__(self, height: int, validators: set[bytes]):
        self.height = height
        self.round = 0
        self.locked = None
        self.valid = None
        self.validators = validators
        self.proposer = get_proposer(height, self.round, validators)

    def new_round(self) -> None:
        self.round += 1
        self.proposer = get_proposer(self.height, self.round, self.validators)

    def lock(self, round: int, id: bytes) -> None:
        self.locked = {"round": round, "id": id}

    def newvalid(self, round: int, id: bytes) -> None:
        self.valid = {"round": round, "id": id}
