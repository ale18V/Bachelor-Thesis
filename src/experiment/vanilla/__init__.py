from experiment.config import NUM_NODES
import click
import experiment.plot


@click.command()
@click.option("--plot", is_flag=True, type=bool, help="Plots the results")
@click.option("--plot-path", type=str, help="Saves the plot to path")
@click.option("--malicious", type=bool, is_flag=True, default=False, help="Run the experiment with malicious nodes")
def cli(plot: bool, plot_path: str, malicious: bool) -> None:
    from experiment.vanilla.client import honest_client, possibly_malicious_client
    from experiment.vanilla.server import server, metrics
    import flwr.simulation

    flwr.simulation.run_simulation(
        server_app=server,
        client_app=honest_client if not malicious else possibly_malicious_client,
        num_supernodes=NUM_NODES,
        verbose_logging=True,
        backend_config={"client_resources": {"num_cpus": 2, "num_gpus": 0}},
    )

    if plot:
        experiment.plot.plot(metrics, path=plot_path, show=True)
