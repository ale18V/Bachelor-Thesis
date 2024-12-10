"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\npeer.proto\x1a\x1bgoogle/protobuf/empty.proto":\n\x14RequestPeersResponse\x12"\n\taddresses\x18\x01 \x03(\x0b2\x0f.NetworkAddress"+\n\x11BlockchainMessage\x12\x16\n\x06blocks\x18\x01 \x03(\x0b2\x06.Block"2\n\x0eBalanceRequest\x12\x14\n\x07address\x18\x01 \x01(\x0cH\x00\x88\x01\x01B\n\n\x08_address"3\n\x0fBalanceResponse\x12\x14\n\x07balance\x18\x01 \x01(\x04H\x00\x88\x01\x01B\n\n\x08_balance"^\n\x13ProposeBlockRequest\x12\x15\n\x05block\x18\x01 \x01(\x0b2\x06.Block\x12\r\n\x05round\x18\x04 \x01(\x04\x12\x0e\n\x06pubkey\x18\x02 \x01(\x0c\x12\x11\n\tsignature\x18\x03 \x01(\x0c"\x83\x01\n\x0ePrevoteMessage\x12\x11\n\x04hash\x18\x01 \x01(\x0cH\x00\x88\x01\x01\x12\x0e\n\x06height\x18\x05 \x01(\x04\x12\r\n\x05round\x18\x06 \x01(\x04\x12\x0e\n\x06pubkey\x18\x02 \x01(\x0c\x12\x11\n\tsignature\x18\x03 \x01(\x0c\x12\x13\n\x0binvalid_txs\x18\x04 \x03(\x0cB\x07\n\x05_hash"p\n\x10PrecommitMessage\x12\x11\n\x04hash\x18\x01 \x01(\x0cH\x00\x88\x01\x01\x12\x0e\n\x06height\x18\x05 \x01(\x04\x12\r\n\x05round\x18\x06 \x01(\x04\x12\x0e\n\x06pubkey\x18\x02 \x01(\x0c\x12\x11\n\tsignature\x18\x03 \x01(\x0cB\x07\n\x05_hash"\x1c\n\x0cBlockRequest\x12\x0c\n\x04hash\x18\x01 \x01(\x0c"5\n\rBlockResponse\x12\x1a\n\x05block\x18\x01 \x01(\x0b2\x06.BlockH\x00\x88\x01\x01B\x08\n\x06_block"!\n\x0eNetworkAddress\x12\x0f\n\x07address\x18\x01 \x01(\t"?\n\x05Block\x12\x1c\n\x06header\x18\x01 \x01(\x0b2\x0c.BlockHeader\x12\x18\n\x04body\x18\x02 \x01(\x0b2\n.BlockBody"c\n\x0bBlockHeader\x12\x0e\n\x06height\x18\x01 \x01(\x04\x12\x13\n\x0bvalid_round\x18\x04 \x01(\x03\x12\x11\n\ttimestamp\x18\x02 \x01(\x04\x12\x0e\n\x06parent\x18\x03 \x01(\x0c\x12\x0c\n\x04hash\x18\x07 \x01(\x0c"/\n\tBlockBody\x12"\n\x0ctransactions\x18\x01 \x03(\x0b2\x0c.Transaction"g\n\x0bTransaction\x12\x12\n\npublic_key\x18\x01 \x01(\x0c\x12\x11\n\tsignature\x18\x02 \x01(\x0c\x12\x11\n\ttimestamp\x18\x03 \x01(\r\x12\x1e\n\x04data\x18\x05 \x01(\x0b2\x10.TransactionData"\x8d\x01\n\x0fTransactionData\x12(\n\x08coinbase\x18\x06 \x01(\x0b2\x14.CoinbaseTransactionH\x00\x12"\n\x05stake\x18\x08 \x01(\x0b2\x11.StakeTransactionH\x00\x12$\n\x06update\x18\t \x01(\x0b2\x12.UpdateTransactionH\x00B\x06\n\x04body"T\n\x11UpdateTransaction\x12\r\n\x05block\x18\x02 \x01(\x0c\x12\x0c\n\x04data\x18\x01 \x03(\x0c\x12\x15\n\x08metadata\x18\x03 \x01(\tH\x00\x88\x01\x01B\x0b\n\t_metadata"+\n\x06Reward\x12\x0f\n\x07address\x18\x01 \x01(\x0c\x12\x10\n\x08quantity\x18\x02 \x01(\x04"/\n\x13CoinbaseTransaction\x12\x18\n\x07rewards\x18\x01 \x03(\x0b2\x07.Reward"$\n\x10StakeTransaction\x12\x10\n\x08quantity\x18\x02 \x01(\x04"1\n\x0cStakeAddress\x12\x0f\n\x07address\x18\x01 \x01(\x0c\x12\x10\n\x08quantity\x18\x02 \x01(\x04")\n\x04Vote\x12\x0f\n\x07address\x18\x01 \x01(\x0c\x12\x10\n\x08quantity\x18\x03 \x01(\x042\xea\x04\n\x04Node\x12:\n\rAdvertisePeer\x12\x0f.NetworkAddress\x1a\x16.google.protobuf.Empty"\x00\x12?\n\x0cRequestPeers\x12\x16.google.protobuf.Empty\x1a\x15.RequestPeersResponse"\x00\x12>\n\x14AdvertiseTransaction\x12\x0c.Transaction\x1a\x16.google.protobuf.Empty"\x00\x12>\n\x0cProposeBlock\x12\x14.ProposeBlockRequest\x1a\x16.google.protobuf.Empty"\x00\x12/\n\x0cRequestBlock\x12\r.BlockRequest\x1a\x0e.BlockResponse"\x00\x12=\n\x10AdvertisePrevote\x12\x0f.PrevoteMessage\x1a\x16.google.protobuf.Empty"\x00\x12A\n\x12AdvertisePrecommit\x12\x11.PrecommitMessage\x1a\x16.google.protobuf.Empty"\x00\x12A\n\x11RequestBlockchain\x12\x16.google.protobuf.Empty\x1a\x12.BlockchainMessage"\x00\x125\n\x0eRequestBalance\x12\x0f.BalanceRequest\x1a\x10.BalanceResponse"\x00\x128\n\x04Ping\x12\x16.google.protobuf.Empty\x1a\x16.google.protobuf.Empty"\x00b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'peer_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
    DESCRIPTOR._options = None
    _globals['_REQUESTPEERSRESPONSE']._serialized_start = 43
    _globals['_REQUESTPEERSRESPONSE']._serialized_end = 101
    _globals['_BLOCKCHAINMESSAGE']._serialized_start = 103
    _globals['_BLOCKCHAINMESSAGE']._serialized_end = 146
    _globals['_BALANCEREQUEST']._serialized_start = 148
    _globals['_BALANCEREQUEST']._serialized_end = 198
    _globals['_BALANCERESPONSE']._serialized_start = 200
    _globals['_BALANCERESPONSE']._serialized_end = 251
    _globals['_PROPOSEBLOCKREQUEST']._serialized_start = 253
    _globals['_PROPOSEBLOCKREQUEST']._serialized_end = 347
    _globals['_PREVOTEMESSAGE']._serialized_start = 350
    _globals['_PREVOTEMESSAGE']._serialized_end = 481
    _globals['_PRECOMMITMESSAGE']._serialized_start = 483
    _globals['_PRECOMMITMESSAGE']._serialized_end = 595
    _globals['_BLOCKREQUEST']._serialized_start = 597
    _globals['_BLOCKREQUEST']._serialized_end = 625
    _globals['_BLOCKRESPONSE']._serialized_start = 627
    _globals['_BLOCKRESPONSE']._serialized_end = 680
    _globals['_NETWORKADDRESS']._serialized_start = 682
    _globals['_NETWORKADDRESS']._serialized_end = 715
    _globals['_BLOCK']._serialized_start = 717
    _globals['_BLOCK']._serialized_end = 780
    _globals['_BLOCKHEADER']._serialized_start = 782
    _globals['_BLOCKHEADER']._serialized_end = 881
    _globals['_BLOCKBODY']._serialized_start = 883
    _globals['_BLOCKBODY']._serialized_end = 930
    _globals['_TRANSACTION']._serialized_start = 932
    _globals['_TRANSACTION']._serialized_end = 1035
    _globals['_TRANSACTIONDATA']._serialized_start = 1038
    _globals['_TRANSACTIONDATA']._serialized_end = 1179
    _globals['_UPDATETRANSACTION']._serialized_start = 1181
    _globals['_UPDATETRANSACTION']._serialized_end = 1265
    _globals['_REWARD']._serialized_start = 1267
    _globals['_REWARD']._serialized_end = 1310
    _globals['_COINBASETRANSACTION']._serialized_start = 1312
    _globals['_COINBASETRANSACTION']._serialized_end = 1359
    _globals['_STAKETRANSACTION']._serialized_start = 1361
    _globals['_STAKETRANSACTION']._serialized_end = 1397
    _globals['_STAKEADDRESS']._serialized_start = 1399
    _globals['_STAKEADDRESS']._serialized_end = 1448
    _globals['_VOTE']._serialized_start = 1450
    _globals['_VOTE']._serialized_end = 1491
    _globals['_NODE']._serialized_start = 1494
    _globals['_NODE']._serialized_end = 2112