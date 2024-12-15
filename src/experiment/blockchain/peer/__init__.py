import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
import loguru
from ..models import AggregationStrategy, ValidationStrategy
from ..training import FedAvgAggregation, TrainingService
from blockchain.node import Node
from blockchain.constants import BOOTSTRAP_NODE_ADDRESS
from blockchain.models import NetworkConfig, NodeConfig
from blockchain.generated.peer_pb2 import Block
import json
from blockchain.bus import EventType
from experiment import config, model
from experiment.blockchain import serialization
from experiment.metrics import MetricsStore


class FederationParticipant(object):
    def __init__(
        self, id: int, port: int, malicious: bool, validation_strategy: Optional[ValidationStrategy] = None
    ) -> None:
        self.id = id
        self.port = port
        self.malicious = malicious
        self.validation = validation_strategy
        loguru.logger.info(f"Node {self.id} created and is validator: {self.validation is not None}")
        self.node = Node(
            NodeConfig(
                become_validator=self.validation is not None,
                validate_fn=self.validation.validate if self.validation else None,
                network=NetworkConfig(port=self.port, peers=set([BOOTSTRAP_NODE_ADDRESS])),
            )
        )
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.metrics = MetricsStore()
        self.global_model = model.Net()
        self.aggregation: AggregationStrategy = FedAvgAggregation(self.global_model)

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
        updates = map(
            lambda tx: tx.data.update,
            filter(lambda tx: tx.data.WhichOneof("body") == "update", block.body.transactions),
        )
        update = self.aggregation.aggregate(updates)
        if update:
            net, malicious_ratio = update
            loguru.logger.info(f"Node {self.id} received an update")
            self.global_model.load_state_dict(net.state_dict())

            loss, accuracy = model.test(net, self.testloader)
            self.metrics.update(block.header.height, accuracy, loss, malicious_ratio)
            if self.validation:
                self.validation.update(net)
            if len(self.metrics) >= config.NUM_ROUNDS:
                await self.stop()
                return
            del net

        if block.header.height > 2 * config.NUM_ROUNDS:
            # We are committing empty blocks as model is accurate and no txs are passing validation anymore
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
            del updated_net

    async def stop(self):
        loguru.logger.info(f"Node {self.id} stopping")
        await self.node.stop()
