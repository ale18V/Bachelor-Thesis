import click
import flwr
from . import malicious_client_fn


@click.command()
def main(id):
    flwr.client.start_client(server_address="localhost:8080", client_fn=malicious_client_fn)


main()
