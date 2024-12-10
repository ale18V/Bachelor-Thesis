from .generated import peer_pb2

GRACE_PERIOD = 10
NUM_CONNECTED_PEERS = 12
DEFAULT_PORT = 6969
BOOTSTRAP_NODE_PORT = DEFAULT_PORT
BOOTSTRAP_NODE_HOST = "localhost"
BOOTSTRAP_NODE_ADDRESS = f"{BOOTSTRAP_NODE_HOST}:{BOOTSTRAP_NODE_PORT}"
BOOTSTRAP_PUBKEY = bytes.fromhex("83e9ebbced447b59a8a51c437f076bfde05815b803f7a6923a639957a63d6f5de285d0c0b461439c0590a7cc41128b299b4a17cd63386c5084c6b734c15a4cda")  # noqa
BOOTSTRAP_PRIVKEY = bytes.fromhex("2fe4819a8220271725c543a000c00dad7c0e45030699f3d78379a739c0462d5e")
SIGNATURE = b"signature"


def makevalidator(pubkeys: list[bytes]) -> list[peer_pb2.Transaction]:
    txs = []
    for pubkey in pubkeys:
        coinbase_tx = peer_pb2.TransactionData(
            coinbase=peer_pb2.CoinbaseTransaction(
                rewards=[
                    peer_pb2.Reward(
                        address=BOOTSTRAP_PUBKEY,
                        quantity=1000,
                    )
                ]
            )
        )

        stake_tx = peer_pb2.TransactionData(
            stake=peer_pb2.StakeTransaction(
                quantity=1000,
            )
        )
        txs.append(
            peer_pb2.Transaction(
                timestamp=0,
                public_key=pubkey,
                signature=SIGNATURE,
                data=coinbase_tx,
            )
        )
        txs.append(
            peer_pb2.Transaction(
                timestamp=0,
                public_key=pubkey,
                signature=SIGNATURE,
                data=stake_tx,
            )
        )
    return txs


genesis = makevalidator([BOOTSTRAP_PUBKEY])

GENESIS_BLOCK = peer_pb2.Block(
    header=peer_pb2.BlockHeader(hash=b"genesis", parent=b"genesis", valid_round=0, timestamp=0, height=0),
    body=peer_pb2.BlockBody(transactions=genesis),
)

PING_TIMEOUT = 60 * 2
# Delay before voting proposing or precommitting
ACTION_DELAY = 1
# If the node doesn't receive at least 2/3 precommits confirming the block within this timeout it will start a new round
PRECOMMIT_TIMEOUT = ACTION_DELAY * 4
# If the node doesn't receive at least 2/3 pre-votes confirming the block within this timeout it will send a null commit
PREVOTE_TIMEOUT = ACTION_DELAY * 6
# If the node doesn't receive any blocks it will cast a null vote
PROPOSE_TIMEOUT = ACTION_DELAY * 8

CONSTANT_REWARD_QUANTITY = 1000
