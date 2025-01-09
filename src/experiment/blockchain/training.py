from collections import OrderedDict
import json
import threading
from typing import Optional
from blockchain.generated.peer_pb2 import Block
import loguru
import numpy
import torch
from experiment import config, model
from experiment.blockchain.serialization import deserialize_params
from experiment.metrics import MetricsStore
from torch.utils.data import DataLoader


class FedAvgAggregator(object):
    def aggregate(self, net: model.Net, block: Block) -> Optional[tuple[OrderedDict[str, torch.Tensor], float]]:
        ml_updates = [tx.data.update for tx in filter(lambda tx: tx.data.HasField("update"), block.body.transactions)]
        if not ml_updates:
            return None
        all_params = [deserialize_params(update.data) for update in ml_updates]

        weights = [
            numpy.average(
                layer,
                axis=0,
            )
            for layer in zip(*all_params)
        ]

        state_dict = OrderedDict(dict(zip(net.state_dict().keys(), (torch.tensor(layer) for layer in weights))))
        return state_dict, sum(1 for _ in filter(lambda tx: json.loads(tx.metadata)["is_malicious"], ml_updates)) / len(
            ml_updates
        )


class TrainingService(object):
    lock = threading.Lock()

    def __init__(self, trainloader: DataLoader, testloader: DataLoader, malicious: bool) -> None:
        self.trainloader = trainloader
        self.testloader = testloader
        self.aggregator = FedAvgAggregator()
        self._is_training = False
        self.metrics = MetricsStore()
        self.is_malicious = malicious
        self.net = model.Net()

    @loguru.logger.catch
    def fit(self, net_state: dict[str, torch.Tensor]) -> tuple[model.Net, bool]:
        self.net.load_state_dict(net_state)
        with self.lock:
            if self._is_training:
                return self.net, self.is_malicious
            self._is_training = True

        model.train(self.net, self.trainloader, config.NUM_EPOCHS)
        if self.is_malicious:
            self.net.apply(model.flip_weights)
        with self.lock:
            self._is_training = False

        return self.net, self.is_malicious

    @property
    def is_training(self) -> bool:
        with self.lock:
            return self._is_training
