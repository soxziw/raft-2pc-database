import Transaction_pb2


class ResumeSerializer:
    def create(clusterId: int, serverId: int):
        resume_request = Transaction_pb2.Resume()
        resume_request.clusterId = clusterId
        resume_request.serverId = serverId
        return resume_request.SerializeToString()