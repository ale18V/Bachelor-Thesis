import random
from ...generated import peer_pb2


def is_valid_round(proposal_req: peer_pb2.ProposeBlockRequest) -> bool:
    return proposal_req.block.header.valid_round >= 0


def get_proposer(height: int, round: int, validators: set[bytes]) -> bytes:
    """
    Returns the proposer for the given height and round.
    """
    if not validators:
        raise Exception("No validators available")
    random.seed(height + round)
    return random.choice(sorted(validators))
