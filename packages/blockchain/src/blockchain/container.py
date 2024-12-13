import asyncio
import os
from typing import Generator
from .models import (
    AbstractBlockchainService,
    AbstractCryptoService,
    AbstractMempoolService,
    AbstractMessageService,
    AbstractNetworkService,
    AbstractValidationService,
)
from .services import (
    ValidationService,
    NodeService,
    MessageService,
    BlockchainService,
    CryptoService,
    MempoolService,
    NetworkService,
)

from .server import NodeServer
from .bus import EventBus
from dependency_injector import containers, providers
from dependency_injector.providers import Provider


def init_event_loop(debug: bool = False) -> Generator[asyncio.AbstractEventLoop, None, None]:
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = None
    if not loop:
        loop = asyncio.new_event_loop()
        loop.set_debug(__name__ == "__main__" or debug)
    asyncio.set_event_loop(loop)
    yield loop
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    message_service: Provider[AbstractMessageService] = providers.Singleton(MessageService)
    loop: Provider[asyncio.AbstractEventLoop] = providers.Resource(init_event_loop, debug=os.getenv("DEBUG", False))
    bus: Provider[EventBus] = providers.Singleton(EventBus, loop=loop)
    validation_service: Provider[AbstractValidationService] = providers.Singleton(ValidationService, config.validate_fn)
    blockchain_service: Provider[AbstractBlockchainService] = providers.Singleton(BlockchainService, bus=bus)
    crypto_service: Provider[AbstractCryptoService] = providers.Singleton(CryptoService, kpriv=config.kpriv)
    mempool_service: Provider[AbstractMempoolService] = providers.Singleton(MempoolService, bus=bus)
    network_service: Provider[AbstractNetworkService] = providers.Singleton(
        NetworkService, config=config.network, loop=loop
    )

    node_service = providers.Factory(
        NodeService,
        blockchain=blockchain_service,
        mempool=mempool_service,
        crypto=crypto_service,
        network=network_service,
        validation=validation_service,
    )

    server: Provider[NodeServer] = providers.Singleton(
        NodeServer,
        config=config.network,
        network_service=network_service,
        blockchain_service=blockchain_service,
        mempool_service=mempool_service,
        message_queue=message_service,
        crypto_service=crypto_service,
    )
