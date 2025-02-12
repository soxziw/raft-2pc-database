import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from proto.stop_pb2 import Stop


class StopSerializer:

    def to_str(clusterId: int, serverId: int):
        stop_request = Stop()
        stop_request.clusterId = clusterId
        stop_request.serverId = serverId
        return stop_request.SerializeToString()
    
    def parse(stop_request_str: bytes):
        stop_request = Stop()
        stop_request.ParseFromString(stop_request_str)
        return stop_request