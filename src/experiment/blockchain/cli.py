import asyncio
from concurrent.futures import ProcessPoolExecutor
from multiprocessing.context import SpawnContext
import time
import blockchain
import click
from blockchain.node import BootstrapNode
import numpy
from experiment import config, utils
from .validation import DatasetAccuracyValidation
from experiment.metrics import MetricsStore
import experiment.plot
from experiment.blockchain.peer import FederationParticipant


def run_participant(id: int, port: int, malicious: bool, validator: int | None) -> MetricsStore:
    import blockchain
    import experiment.model

    blockchain.enable_logging(use_custom_fmt=True, disable=["server", "network"])
    validation = None
    if validator is not None:
        valloader = experiment.model.load_validation_dataset(
            partition_id=validator, num_validators=config.NUM_VALIDATORS
        )
        validation = DatasetAccuracyValidation(valloader)
    participant = FederationParticipant(id, port, malicious, validation)
    return participant.run()


@click.command()
@click.option("--bootstrap/--no-bootstrap", is_flag=True, default=True, help="Run/Don't run the bootstrap node")
@click.option("--plot-all", is_flag=True, default=False, help="Plot metrics for each participant")
@click.option("--malicious", is_flag=True, default=False, help="Run the experiment with malicious nodes")
def cli(bootstrap: bool, plot_all: bool, malicious: bool):
    if bootstrap:
        bootstrap_node = BootstrapNode()

    loop = asyncio.get_event_loop()
    # Don't want to fork because it may cause some problems as grpc server is multithreaded
    executor = ProcessPoolExecutor(max_workers=config.NUM_NODES, mp_context=SpawnContext())
    seed = int(time.time())
    malicious_participants = (
        utils.get_malicious_actors_ids(config.NUM_NODES, seed, config.MALICIOUS_RATIO) if malicious else []
    )
    validator_participants = utils.get_validators_ids(
        config.NUM_NODES, malicious_participants, seed, config.NUM_VALIDATORS
    )
    print(f"Malicious participants: {malicious_participants}")
    print(f"Validator participants: {validator_participants}")

    async def run_federation():
        futures = [
            loop.run_in_executor(
                executor,
                run_participant,
                *(
                    i,
                    8000 + 10 * i,
                    i in malicious_participants,
                    validator_participants.index(i) if i in validator_participants else None,
                ),
            )
            for i in range(config.NUM_NODES)
        ]
        done, _ = await asyncio.wait(futures)
        results = [el.result() for el in done]
        if bootstrap:
            await bootstrap_node.stop()

        if plot_all:
            for i, result in enumerate(results):
                experiment.plot.plot(metrics=result, path=f"blockchain-{i}")

        aggregate = {}
        for metric in results:
            for height, (accuracy, loss, malicious) in metric.get_dict().items():
                if height not in aggregate:
                    aggregate[height] = []
                aggregate[height].append((accuracy, loss, malicious))

        for h in aggregate.keys():
            aggregate[h] = tuple(numpy.average(aggregate[h], axis=0))
        metrics = MetricsStore(aggregate)

        experiment.plot.plot(
            metrics=metrics,
            show=True,
            path="blockchain",
        )

    if bootstrap:
        loop.create_task(run_federation())
        blockchain.enable_logging(use_custom_fmt=True)
        bootstrap_node.run()
    else:
        loop.run_until_complete(run_federation())
