from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union
DESCRIPTOR: _descriptor.FileDescriptor

class RequestPeersResponse(_message.Message):
    __slots__ = ('addresses',)
    ADDRESSES_FIELD_NUMBER: _ClassVar[int]
    addresses: _containers.RepeatedCompositeFieldContainer[NetworkAddress]

    def __init__(self, addresses: _Optional[_Iterable[_Union[NetworkAddress, _Mapping]]]=...) -> None:
        ...

class BlockchainMessage(_message.Message):
    __slots__ = ('blocks',)
    BLOCKS_FIELD_NUMBER: _ClassVar[int]
    blocks: _containers.RepeatedCompositeFieldContainer[Block]

    def __init__(self, blocks: _Optional[_Iterable[_Union[Block, _Mapping]]]=...) -> None:
        ...

class BalanceRequest(_message.Message):
    __slots__ = ('address',)
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    address: bytes

    def __init__(self, address: _Optional[bytes]=...) -> None:
        ...

class BalanceResponse(_message.Message):
    __slots__ = ('balance',)
    BALANCE_FIELD_NUMBER: _ClassVar[int]
    balance: int

    def __init__(self, balance: _Optional[int]=...) -> None:
        ...

class ProposeBlockRequest(_message.Message):
    __slots__ = ('block', 'round', 'pubkey', 'signature')
    BLOCK_FIELD_NUMBER: _ClassVar[int]
    ROUND_FIELD_NUMBER: _ClassVar[int]
    PUBKEY_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    block: Block
    round: int
    pubkey: bytes
    signature: bytes

    def __init__(self, block: _Optional[_Union[Block, _Mapping]]=..., round: _Optional[int]=..., pubkey: _Optional[bytes]=..., signature: _Optional[bytes]=...) -> None:
        ...

class PrevoteMessage(_message.Message):
    __slots__ = ('hash', 'height', 'round', 'pubkey', 'signature')
    HASH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    ROUND_FIELD_NUMBER: _ClassVar[int]
    PUBKEY_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    hash: bytes
    height: int
    round: int
    pubkey: bytes
    signature: bytes

    def __init__(self, hash: _Optional[bytes]=..., height: _Optional[int]=..., round: _Optional[int]=..., pubkey: _Optional[bytes]=..., signature: _Optional[bytes]=...) -> None:
        ...

class PrecommitMessage(_message.Message):
    __slots__ = ('hash', 'height', 'round', 'pubkey', 'signature')
    HASH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    ROUND_FIELD_NUMBER: _ClassVar[int]
    PUBKEY_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    hash: bytes
    height: int
    round: int
    pubkey: bytes
    signature: bytes

    def __init__(self, hash: _Optional[bytes]=..., height: _Optional[int]=..., round: _Optional[int]=..., pubkey: _Optional[bytes]=..., signature: _Optional[bytes]=...) -> None:
        ...

class BlockRequest(_message.Message):
    __slots__ = ('hash',)
    HASH_FIELD_NUMBER: _ClassVar[int]
    hash: bytes

    def __init__(self, hash: _Optional[bytes]=...) -> None:
        ...

class BlockResponse(_message.Message):
    __slots__ = ('block',)
    BLOCK_FIELD_NUMBER: _ClassVar[int]
    block: Block

    def __init__(self, block: _Optional[_Union[Block, _Mapping]]=...) -> None:
        ...

class NetworkAddress(_message.Message):
    __slots__ = ('address',)
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    address: str

    def __init__(self, address: _Optional[str]=...) -> None:
        ...

class Block(_message.Message):
    __slots__ = ('header', 'body')
    HEADER_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    header: BlockHeader
    body: BlockBody

    def __init__(self, header: _Optional[_Union[BlockHeader, _Mapping]]=..., body: _Optional[_Union[BlockBody, _Mapping]]=...) -> None:
        ...

class BlockHeader(_message.Message):
    __slots__ = ('height', 'valid_round', 'timestamp', 'parent', 'hash')
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    VALID_ROUND_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    PARENT_FIELD_NUMBER: _ClassVar[int]
    HASH_FIELD_NUMBER: _ClassVar[int]
    height: int
    valid_round: int
    timestamp: int
    parent: bytes
    hash: bytes

    def __init__(self, height: _Optional[int]=..., valid_round: _Optional[int]=..., timestamp: _Optional[int]=..., parent: _Optional[bytes]=..., hash: _Optional[bytes]=...) -> None:
        ...

class BlockBody(_message.Message):
    __slots__ = ('transactions',)
    TRANSACTIONS_FIELD_NUMBER: _ClassVar[int]
    transactions: _containers.RepeatedCompositeFieldContainer[Transaction]

    def __init__(self, transactions: _Optional[_Iterable[_Union[Transaction, _Mapping]]]=...) -> None:
        ...

class Transaction(_message.Message):
    __slots__ = ('public_key', 'signature', 'timestamp', 'id', 'data')
    PUBLIC_KEY_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    public_key: bytes
    signature: bytes
    timestamp: int
    id: bytes
    data: TransactionData

    def __init__(self, public_key: _Optional[bytes]=..., signature: _Optional[bytes]=..., timestamp: _Optional[int]=..., id: _Optional[bytes]=..., data: _Optional[_Union[TransactionData, _Mapping]]=...) -> None:
        ...

class TransactionData(_message.Message):
    __slots__ = ('coinbase', 'stake', 'update')
    COINBASE_FIELD_NUMBER: _ClassVar[int]
    STAKE_FIELD_NUMBER: _ClassVar[int]
    UPDATE_FIELD_NUMBER: _ClassVar[int]
    coinbase: CoinbaseTransaction
    stake: StakeTransaction
    update: UpdateTransaction

    def __init__(self, coinbase: _Optional[_Union[CoinbaseTransaction, _Mapping]]=..., stake: _Optional[_Union[StakeTransaction, _Mapping]]=..., update: _Optional[_Union[UpdateTransaction, _Mapping]]=...) -> None:
        ...

class UpdateTransaction(_message.Message):
    __slots__ = ('block', 'data', 'metadata')
    BLOCK_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    block: bytes
    data: _containers.RepeatedScalarFieldContainer[bytes]
    metadata: str

    def __init__(self, block: _Optional[bytes]=..., data: _Optional[_Iterable[bytes]]=..., metadata: _Optional[str]=...) -> None:
        ...

class Reward(_message.Message):
    __slots__ = ('address', 'quantity')
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    address: bytes
    quantity: int

    def __init__(self, address: _Optional[bytes]=..., quantity: _Optional[int]=...) -> None:
        ...

class CoinbaseTransaction(_message.Message):
    __slots__ = ('rewards',)
    REWARDS_FIELD_NUMBER: _ClassVar[int]
    rewards: _containers.RepeatedCompositeFieldContainer[Reward]

    def __init__(self, rewards: _Optional[_Iterable[_Union[Reward, _Mapping]]]=...) -> None:
        ...

class StakeTransaction(_message.Message):
    __slots__ = ('quantity',)
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    quantity: int

    def __init__(self, quantity: _Optional[int]=...) -> None:
        ...

class StakeAddress(_message.Message):
    __slots__ = ('address', 'quantity')
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    address: bytes
    quantity: int

    def __init__(self, address: _Optional[bytes]=..., quantity: _Optional[int]=...) -> None:
        ...

class Vote(_message.Message):
    __slots__ = ('address', 'quantity')
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    QUANTITY_FIELD_NUMBER: _ClassVar[int]
    address: bytes
    quantity: int

    def __init__(self, address: _Optional[bytes]=..., quantity: _Optional[int]=...) -> None:
        ...