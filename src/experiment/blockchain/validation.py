from typing import Iterable, override
import torch
from torch.utils.data import DataLoader
from experiment import model
from experiment.blockchain import serialization
from blockchain.generated.peer_pb2 import UpdateTransaction

from .models import ValidationStrategy


class DatasetAccuracyValidation(ValidationStrategy):
    def __init__(self, valloader: DataLoader) -> None:
        self.valloader = valloader
        self.last_accuracy = 0.0

    def validate_tx(self, data: UpdateTransaction):
        net = serialization.deserialize_model(data)
        loss, accuracy = model.test(net=net, testloader=self.valloader)
        return 1.5 * accuracy < self.last_accuracy

    @override
    def validate(self, block: Iterable[UpdateTransaction]) -> Iterable[bool]:
        return map(lambda tx: self.validate_tx(tx), block)

    @override
    def update(self, net: torch.nn.Module) -> None:
        _, self.last_accuracy = model.test(net, self.valloader)
