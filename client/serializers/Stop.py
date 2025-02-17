import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from proto.stop_pb2 import Stop
from proto.wrapperMessage_pb2 import WrapperMessage


class StopSerializer:

    def to_str(clusterId: int, serverId: int):
        stop_request = Stop()
        stop_request.clusterId = clusterId
        stop_request.serverId = serverId
        return WrapperMessage(stop=stop_request).SerializeToString()
    
    def parse(stop_request_str: bytes):
        wrapper = WrapperMessage()
        wrapper.ParseFromString(stop_request_str)
        if wrapper.HasField("stop"):
            return wrapper.stop