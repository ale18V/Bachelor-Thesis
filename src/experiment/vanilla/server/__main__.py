import click
import flwr
from . import server_config, strategy, metrics
import experiment.plot


@click.command()
@click.argument("path", type=str)
def main(path) -> None:
    flwr.server.start_server(server_address="0.0.0.0:8080", config=server_config, strategy=strategy)
    experiment.plot.plot(metrics, path=path, show=True)


main()
