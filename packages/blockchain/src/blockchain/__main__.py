import click
from .node import BootstrapNode, Node, WebGui
from .constants import BOOTSTRAP_NODE_ADDRESS, DEFAULT_PORT
from .models import NetworkConfig, NodeConfig


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option("--web-gui/--no-web-gui", default=False, help="Start the web GUI")
def bootstrap(web_gui: bool) -> None:
    """
    Start a bootstrapping node.
    """
    node = BootstrapNode()
    if web_gui:
        gui = WebGui(blockchain_service=node.blockchain, network_service=node.network, port=8080)
        gui.run()
    node.run()


@cli.command()
@click.argument("port", type=int, default=DEFAULT_PORT)
@click.argument("peers", nargs=-1)
@click.option("--become-validator", is_flag=True, default=False, help="Become a validator node")
@click.option("--private-key", type=str, default=None, help="Private key to use (hex)")
def run(port: int, peers: list[str], become_validator: bool, private_key: str) -> None:
    """
    Run a node of the blockchain.
    """

    Node(
        NodeConfig(
            network=NetworkConfig(port=port, peers=set(peers) if peers else set([BOOTSTRAP_NODE_ADDRESS])),
            kpriv=bytes.fromhex(private_key) if private_key else None,
            become_validator=become_validator,
            validate_fn=lambda *args: True,
        )
    ).run()


if __name__ == "__main__":
    cli()
