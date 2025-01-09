from flwr.client import ClientApp, NumPyClient
from flwr.common import Context
from experiment import utils
from experiment.model import Net, train, test, load_datasets, malicious_transforomation, DEVICE
import experiment.config
from .serialization import get_parameters, set_parameters


class FlowerClient(NumPyClient):
    def __init__(self, net, trainloader, valloader, is_malicious=False):
        self.net = net
        self.trainloader = trainloader
        self.valloader = valloader
        self.is_malicious = is_malicious

    def get_parameters(self, config):
        return get_parameters(self.net)

    def fit(self, parameters, config):
        set_parameters(self.net, parameters)
        train(self.net, self.trainloader, epochs=experiment.config.NUM_EPOCHS)
        if self.is_malicious:
            self.net.apply(malicious_transforomation)
        return get_parameters(self.net), len(self.trainloader), {}

    def evaluate(self, parameters, config):
        set_parameters(self.net, parameters)
        loss, accuracy = test(self.net, self.valloader)
        return float(loss), len(self.valloader), {"accuracy": float(accuracy), "is_malicious": self.is_malicious}


def malicious_client_fn(context: Context):
    model = Net().to(DEVICE)
    # Set by flwr
    partition_id = int(context.node_config["partition-id"])

    if "is_malicious" not in context.node_config:
        context.node_config["is_malicious"] = partition_id in utils.get_malicious_actors_ids(
            num_nodes=experiment.config.NUM_NODES, seed=context.run_id, ratio=experiment.config.MALICIOUS_RATIO
        )

    trainloader, valloader, _ = load_datasets(partition_id=partition_id)
    print(f"Client {partition_id} loaded datasets")

    return FlowerClient(model, trainloader, valloader, is_malicious=context.node_config["is_malicious"]).to_client()


def honest_client_fn(context: Context):
    model = Net().to(DEVICE)
    # Set by flwr
    partition_id = int(context.node_config["partition-id"])

    trainloader, valloader, _ = load_datasets(partition_id=partition_id)
    print(f"Client {partition_id} loaded datasets")
    return FlowerClient(model, trainloader, valloader).to_client()


honest_client = ClientApp(client_fn=honest_client_fn)
possibly_malicious_client = ClientApp(client_fn=malicious_client_fn)
