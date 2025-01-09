import time
from typing import Optional, override
from blockchain.models import AbstractCryptoService
from blockchain.generated import peer_pb2
from ecdsa import SigningKey, NIST256p  # type: ignore


class CryptoService(AbstractCryptoService):
    def __init__(self, kpriv: Optional[bytes] = None) -> None:
        if kpriv:
            self._kpriv = SigningKey.from_string(kpriv, curve=NIST256p)
        else:
            self._kpriv = SigningKey.generate(curve=NIST256p)
        self._kpub: bytes = self._kpriv.get_verifying_key().to_string()

    @override
    def sign_proposal(self, round: int, block: peer_pb2.Block) -> peer_pb2.ProposeBlockRequest:
        msg = peer_pb2.ProposeBlockRequest(round=round, block=block)
        msg.signature = self._kpriv.sign_deterministic(msg.SerializeToString(deterministic=True))
        msg.pubkey = self._kpub
        return msg

    @override
    def sign_prevote(self, height: int, round: int, hash: bytes | None) -> peer_pb2.PrevoteMessage:
        msg = peer_pb2.PrevoteMessage(height=height, round=round, hash=hash)

        msg.signature = self._kpriv.sign_deterministic(msg.SerializeToString(deterministic=True))
        msg.pubkey = self._kpub
        return msg

    @override
    def sign_precommit(self, height: int, round: int, hash: bytes | None) -> peer_pb2.PrecommitMessage:

        msg = peer_pb2.PrecommitMessage(
            height=height,
            round=round,
            hash=hash,
        )

        msg.signature = self._kpriv.sign_deterministic(msg.SerializeToString(deterministic=True))
        msg.pubkey = self._kpub
        return msg

    @override
    def get_pubkey(self) -> bytes:
        return self._kpub

    @override
    def sign_transaction(self, tx_data: peer_pb2.TransactionData) -> peer_pb2.Transaction:
        tx = peer_pb2.Transaction(
            timestamp=int(time.time()),
            data=tx_data,
            public_key=self._kpub,
            signature=self._kpriv.sign_deterministic(tx_data.SerializeToString(deterministic=True)),
        )

        return tx
