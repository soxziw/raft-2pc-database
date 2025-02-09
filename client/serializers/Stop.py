import Transaction_pb2


class StopSerializer:
    def create(clusterId: int, serverId: int):
        stop_request = Transaction_pb2.Stop()
        stop_request.clusterId = clusterId
        stop_request.serverId = serverId
        return stop_request.SerializeToString()