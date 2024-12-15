from abc import ABCMeta, abstractmethod
from typing import Iterable, Optional

from blockchain.generated.peer_pb2 import UpdateTransaction
import torch


class ValidationStrategy(metaclass=ABCMeta):
    @abstractmethod
    def validate(self, data: Iterable[UpdateTransaction]) -> Iterable[bool]:
        raise NotImplementedError

    @abstractmethod
    def update(self, net: torch.nn.Module) -> None:
        raise NotImplementedError


class AggregationStrategy(metaclass=ABCMeta):
    @abstractmethod
    def aggregate(self, data: Iterable[UpdateTransaction]) -> Optional[tuple[torch.nn.Module, float]]:
        raise NotImplementedError
