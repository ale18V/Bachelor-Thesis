import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
import loguru
from ..training import FedAvgAggregator, TrainingService
from blockchain.node import Node
from blockchain.constants import BOOTSTRAP_NODE_ADDRESS
from blockchain.models import NetworkConfig, NodeConfig
from blockchain.generated.peer_pb2 import Block
import json
from blockchain.bus import EventType
from experiment import config, model
from experiment.blockchain import serialization
from experiment.metrics import MetricsStore
from blockchain.generated.peer_pb2 import UpdateTransaction


class FederationParticipant(object):
    def __init__(self, id: int, port: int, malicious: bool, val_id: Optional[int] = None) -> None:
        self.id = id
        self.port = port
        self.malicious = malicious
        self.validator = val_id is not None
        validate_fn = None
        if self.validator:
            self.valloader = model.load_validation_dataset(partition_id=val_id, num_validators=config.NUM_VALIDATORS)
            validate_fn = self._validate
        self.node = Node(
            NodeConfig(
                become_validator=self.validator,
                validate_fn=validate_fn,
                network=NetworkConfig(port=self.port, peers=set([BOOTSTRAP_NODE_ADDRESS])),
            )
        )
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.metrics = MetricsStore()
        self.validation_metrics = MetricsStore()
        self.global_model = model.Net()
        self.aggregator = FedAvgAggregator()

    def run(self) -> MetricsStore:
        self.trainloader, self.testloader, _ = model.load_datasets(partition_id=self.id)
        self.training = TrainingService(
            trainloader=self.trainloader, testloader=self.testloader, malicious=self.malicious
        )
        self.node.bus.subscribe(EventType.UPDATE, self._receive_update)
        try:
            self.node.run()
        except Exception as e:
            loguru.logger.error(f"Node {self.id} failed with {e}")
        finally:
            return self.metrics

    async def _receive_update(self, block: Block):
        if block and (res := self.aggregator.aggregate(block=block, net=self.global_model)):
            loguru.logger.info(f"Node {self.id} received an update")
            state_dict, malicious_ratio = res
            self.global_model.load_state_dict(state_dict)
            loss, accuracy = model.test(self.global_model, self.testloader)
            self.metrics.update(accuracy, loss, malicious_ratio)
            if self.validator:
                loss, accuracy = model.test(self.global_model, self.valloader)
                self.validation_metrics.update(accuracy, loss, malicious_ratio)

            if len(self.metrics) == config.NUM_ROUNDS:
                await self.stop()
                return

        if not self.training.is_training:
            loop = asyncio.get_event_loop()

            updated_net, is_malicious = await loop.run_in_executor(
                self.executor, self.training.fit, self.global_model.state_dict()
            )
            await self.node.utils.broadcast_update(
                data=serialization.serialize_model(updated_net), metadata=json.dumps({"is_malicious": is_malicious})
            )

    def _validate(self, data: UpdateTransaction) -> bool:
        net = serialization.deserialize_model(data)
        loss, accuracy = model.test(net=net, testloader=self.valloader)
        accuracies = self.validation_metrics.accuracy
        if not accuracies:
            return True

        latest_avg_accuracy = accuracies[-1]
        if 1.5 * accuracy < latest_avg_accuracy:
            return False
        return True

    async def stop(self):
        await self.node.stop()
