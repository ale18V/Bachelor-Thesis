import math
import flwr
from flwr.common import EvaluateRes
from flwr.server.client_proxy import ClientProxy
import loguru
import experiment
import experiment.config
from experiment.metrics import MetricsStore


metrics = MetricsStore()


# Custom strategy with logging accuracy
class AccuracyLoggingStrategy(flwr.server.strategy.FedAvg):
    def aggregate_evaluate(
        self,
        server_round: int,
        results: list[tuple[ClientProxy, EvaluateRes]],
        failures: list[tuple[ClientProxy, EvaluateRes] | BaseException],
    ) -> tuple[float | None, dict[str, bool | bytes | float | int | str]]:
        loguru.logger.info(f"Round {server_round} results: {results[1]}")
        data = list(map(lambda x: x[1], results))
        avg_acc = sum(item.num_examples * float(item.metrics["accuracy"]) for item in data) / sum(
            item.num_examples for item in data
        )
        avg_malicious = sum(item.num_examples * int(item.metrics["is_malicious"]) for item in data) / sum(
            item.num_examples for item in data
        )
        res = super().aggregate_evaluate(server_round, results, failures)
        metrics.update(server_round, avg_acc, res[0] or math.nan, avg_malicious)
        return res


# Create FedAvg strategy
strategy = AccuracyLoggingStrategy(
    fraction_fit=1,  # Sample 100% of available clients for training
    fraction_evaluate=1,  # Sample 100% of available clients for evaluation
    min_fit_clients=experiment.config.NUM_NODES,
    min_evaluate_clients=experiment.config.NUM_NODES,
    min_available_clients=experiment.config.NUM_NODES,  # Wait until all nodes are online and available
)

server_config = flwr.server.ServerConfig(num_rounds=experiment.config.NUM_ROUNDS, round_timeout=60 * 3)


def server_fn(context: flwr.common.Context) -> flwr.server.ServerAppComponents:
    """Construct components that set the ServerApp behaviour.

    You can use the settings in `context.run_config` to parameterize the
    construction of all elements (e.g the strategy or the number of rounds)
    wrapped in the returned ServerAppComponents object.
    """

    return flwr.server.ServerAppComponents(config=server_config, strategy=strategy)


server = flwr.server.ServerApp(server_fn=server_fn)
