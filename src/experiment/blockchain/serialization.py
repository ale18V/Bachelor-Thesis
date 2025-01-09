from collections import OrderedDict
from typing import Iterable
import numpy
from flwr.common.parameter import ndarray_to_bytes, bytes_to_ndarray
from blockchain.generated.peer_pb2 import UpdateTransaction
import torch

from experiment import model


def serialize_model(net) -> list[bytes]:
    return [ndarray_to_bytes(val.cpu().numpy()) for _, val in net.state_dict().items()]


def deserialize_params(data: Iterable[bytes]) -> list[numpy.typing.NDArray]:
    params = [bytes_to_ndarray(item) for item in data]
    return params


def deserialize_model(update: UpdateTransaction) -> model.Net:
    weights = deserialize_params(update.data)
    net = model.Net()

    state_dict = OrderedDict(dict(zip(net.state_dict().keys(), (torch.tensor(layer) for layer in weights))))
    net.load_state_dict(state_dict)
    return net
