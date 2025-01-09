import click
from experiment import vanilla, blockchain


@click.group()
def cli():
    pass


cli.add_command(vanilla.cli, name="vanilla")
cli.add_command(blockchain.cli, name="blockchain")


if __name__ == "__main__":
    cli()
