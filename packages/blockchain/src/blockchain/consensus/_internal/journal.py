from typing import Optional, override
from ...models import Commit, MessageLog, Vote, Message
from ...generated import peer_pb2


class MessageLogImpl(MessageLog):
    prevotes: dict[int, set[Vote]]
    precommits: dict[int, set[Commit]]
    proposals: dict[bytes, peer_pb2.Block]

    def __init__(self, threshold: int):
        self.prevotes = {}
        self.precommits = {}
        self.proposals = {}
        self.threshold = threshold

    def count_prevotes_for(self, round: int, hash: bytes | None) -> int:
        return len(list(filter(lambda vote: vote.target == hash, self.prevotes[round])))

    def count_precommits_for(self, round: int, hash: bytes | None) -> int:
        return len(list(filter(lambda commit: commit.target == hash, self.precommits[round])))

    def add_message(self, message: Message) -> bool:
        if isinstance(message, peer_pb2.PrecommitMessage):
            return self.add_precommit(message)
        elif isinstance(message, peer_pb2.PrevoteMessage):
            return self.add_prevote(message)
        elif isinstance(message, peer_pb2.ProposeBlockRequest):
            return self.add_proposal(message)

    def get_candidate(self, hash: bytes) -> Optional[peer_pb2.Block]:
        return self.proposals.get(hash, None)

    def add_precommit(self, precommit: peer_pb2.PrecommitMessage) -> bool:
        if precommit.round not in self.precommits:
            self.precommits[precommit.round] = set()
        commit = Commit(precommit.pubkey, precommit.hash)
        if commit in self.precommits[precommit.round]:
            return False

        self.precommits[precommit.round].add(commit)
        return True

    def add_prevote(self, prevote: peer_pb2.PrevoteMessage) -> bool:
        if prevote.round not in self.prevotes:
            self.prevotes[prevote.round] = set()

        vote = Vote(prevote.pubkey, prevote.hash)
        if vote in self.prevotes[prevote.round]:
            return False

        self.prevotes[prevote.round].add(Vote(prevote.pubkey, prevote.hash))
        return True

    def add_proposal(self, proposal: peer_pb2.ProposeBlockRequest) -> bool:
        hash = proposal.block.header.hash
        if hash in self.proposals:
            return False

        self.proposals[proposal.block.header.hash] = proposal.block
        return True

    def has_precommit_quorum(self, round: int, target: Optional[bytes]) -> bool:
        return self.count_precommits_for(round, target) >= self.threshold

    def has_prevote_quorum(self, round: int, target: Optional[bytes]) -> bool:
        return self.count_prevotes_for(round, target) >= self.threshold

    @override
    def reset(self, threshold: int) -> None:
        self.threshold = threshold
        self.prevotes = {}
        self.precommits = {}
        self.proposals = {}
