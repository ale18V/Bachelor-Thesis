from blockchain.constants import BOOTSTRAP_NODE_HOST, BOOTSTRAP_NODE_PORT, BOOTSTRAP_PRIVKEY
from blockchain.models import NetworkConfig, NodeConfig
from . import Node


class BootstrapNode(Node):
    def __init__(self) -> None:
        super().__init__(
            NodeConfig(
                network=NetworkConfig(port=BOOTSTRAP_NODE_PORT, host=BOOTSTRAP_NODE_HOST),
                kpriv=BOOTSTRAP_PRIVKEY,
            )
        )
