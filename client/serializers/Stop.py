import transaction_pb2


class StopSerializer:

    def create(clusterId: int, serverId: int):
        stop_request = transaction_pb2.Stop()
        stop_request.clusterId = clusterId
        stop_request.serverId = serverId
        return stop_request.SerializeToString()
    
    def parse(stop_request_str: str):
        stop_request = transaction_pb2.Stop()
        stop_request.ParseFromString(stop_request_str)
        return stop_request