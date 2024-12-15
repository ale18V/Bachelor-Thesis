import json
import threading
from typing import Iterable, Optional
from blockchain.generated.peer_pb2 import UpdateTransaction
import loguru
import numpy
import torch
from experiment import config, model
from .models import AggregationStrategy
from experiment.blockchain.serialization import deserialize_params
from experiment.metrics import MetricsStore
from torch.utils.data import DataLoader
from torch import nn


class FedAvgAggregation(AggregationStrategy):
    def __init__(self, net: nn.Module) -> None:
        self.model_keys = net.state_dict().keys()
        self.model_class = net.__class__

    def aggregate(self, txs: Iterable[UpdateTransaction]) -> Optional[tuple[nn.Module, float]]:
        txs = list(txs)
        all_params = [deserialize_params(update.data) for update in txs]
        if not all_params:
            return None

        weights = [
            numpy.average(
                layer,
                axis=0,
            )
            for layer in zip(*all_params)
        ]

        state_dict = {k: v for k, v in zip(self.model_keys, (torch.tensor(layer) for layer in weights))}
        net = self.model_class()
        net.load_state_dict(state_dict)
        return net, sum(1 for _ in filter(lambda tx: json.loads(tx.metadata)["is_malicious"], txs)) / len(
            txs
        )


class TrainingService(object):
    lock = threading.Lock()

    def __init__(self, trainloader: DataLoader, testloader: DataLoader, malicious: bool) -> None:
        self.trainloader = trainloader
        self.testloader = testloader
        self._is_training = False
        self.is_malicious = malicious
        self.metrics = MetricsStore()
        self.net = model.Net()
        self.aggregator = FedAvgAggregation(self.net)

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
