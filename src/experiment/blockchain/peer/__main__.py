import click
from . import FederationParticipant


@click.command()
@click.option("--port", default=5000, help="Port to run the participant on")
@click.option("--validator", is_flag=True, help="Run as a validator")
@click.option("--plot/--no-plot", default=False, help="Plot the results")
def main(port: int, validator: bool, plot: bool):
    metrics = FederationParticipant(id=0, port=port, malicious=False, val_id=0 if validator else None).run()
    if plot:
        from experiment.plot import plot as plot_metrics

        plot_metrics(metrics, show=True)


if __name__ == "__main__":
    main()
