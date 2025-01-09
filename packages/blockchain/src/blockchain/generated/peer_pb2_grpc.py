"""Client and server classes corresponding to protobuf-defined services."""
import grpc
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from . import peer_pb2 as peer__pb2

class NodeStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.AdvertisePeer = channel.unary_unary('/Node/AdvertisePeer', request_serializer=peer__pb2.NetworkAddress.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString)
        self.RequestPeers = channel.unary_unary('/Node/RequestPeers', request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, response_deserializer=peer__pb2.RequestPeersResponse.FromString)
        self.AdvertiseTransaction = channel.unary_unary('/Node/AdvertiseTransaction', request_serializer=peer__pb2.Transaction.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString)
        self.ProposeBlock = channel.unary_unary('/Node/ProposeBlock', request_serializer=peer__pb2.ProposeBlockRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString)
        self.RequestBlock = channel.unary_unary('/Node/RequestBlock', request_serializer=peer__pb2.BlockRequest.SerializeToString, response_deserializer=peer__pb2.BlockResponse.FromString)
        self.AdvertisePrevote = channel.unary_unary('/Node/AdvertisePrevote', request_serializer=peer__pb2.PrevoteMessage.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString)
        self.AdvertisePrecommit = channel.unary_unary('/Node/AdvertisePrecommit', request_serializer=peer__pb2.PrecommitMessage.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString)
        self.RequestBlockchain = channel.unary_unary('/Node/RequestBlockchain', request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, response_deserializer=peer__pb2.BlockchainMessage.FromString)
        self.RequestBalance = channel.unary_unary('/Node/RequestBalance', request_serializer=peer__pb2.BalanceRequest.SerializeToString, response_deserializer=peer__pb2.BalanceResponse.FromString)
        self.Ping = channel.unary_unary('/Node/Ping', request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString)

class NodeServicer(object):
    """Missing associated documentation comment in .proto file."""

    def AdvertisePeer(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RequestPeers(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def AdvertiseTransaction(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ProposeBlock(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RequestBlock(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def AdvertisePrevote(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def AdvertisePrecommit(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RequestBlockchain(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RequestBalance(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Ping(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_NodeServicer_to_server(servicer, server):
    rpc_method_handlers = {'AdvertisePeer': grpc.unary_unary_rpc_method_handler(servicer.AdvertisePeer, request_deserializer=peer__pb2.NetworkAddress.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'RequestPeers': grpc.unary_unary_rpc_method_handler(servicer.RequestPeers, request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, response_serializer=peer__pb2.RequestPeersResponse.SerializeToString), 'AdvertiseTransaction': grpc.unary_unary_rpc_method_handler(servicer.AdvertiseTransaction, request_deserializer=peer__pb2.Transaction.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'ProposeBlock': grpc.unary_unary_rpc_method_handler(servicer.ProposeBlock, request_deserializer=peer__pb2.ProposeBlockRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'RequestBlock': grpc.unary_unary_rpc_method_handler(servicer.RequestBlock, request_deserializer=peer__pb2.BlockRequest.FromString, response_serializer=peer__pb2.BlockResponse.SerializeToString), 'AdvertisePrevote': grpc.unary_unary_rpc_method_handler(servicer.AdvertisePrevote, request_deserializer=peer__pb2.PrevoteMessage.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'AdvertisePrecommit': grpc.unary_unary_rpc_method_handler(servicer.AdvertisePrecommit, request_deserializer=peer__pb2.PrecommitMessage.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'RequestBlockchain': grpc.unary_unary_rpc_method_handler(servicer.RequestBlockchain, request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, response_serializer=peer__pb2.BlockchainMessage.SerializeToString), 'RequestBalance': grpc.unary_unary_rpc_method_handler(servicer.RequestBalance, request_deserializer=peer__pb2.BalanceRequest.FromString, response_serializer=peer__pb2.BalanceResponse.SerializeToString), 'Ping': grpc.unary_unary_rpc_method_handler(servicer.Ping, request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('Node', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))

class Node(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def AdvertisePeer(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Node/AdvertisePeer', peer__pb2.NetworkAddress.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def RequestPeers(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Node/RequestPeers', google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, peer__pb2.RequestPeersResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def AdvertiseTransaction(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Node/AdvertiseTransaction', peer__pb2.Transaction.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def ProposeBlock(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Node/ProposeBlock', peer__pb2.ProposeBlockRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def RequestBlock(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Node/RequestBlock', peer__pb2.BlockRequest.SerializeToString, peer__pb2.BlockResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def AdvertisePrevote(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Node/AdvertisePrevote', peer__pb2.PrevoteMessage.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def AdvertisePrecommit(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Node/AdvertisePrecommit', peer__pb2.PrecommitMessage.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def RequestBlockchain(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Node/RequestBlockchain', google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, peer__pb2.BlockchainMessage.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def RequestBalance(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Node/RequestBalance', peer__pb2.BalanceRequest.SerializeToString, peer__pb2.BalanceResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Ping(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Node/Ping', google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata)