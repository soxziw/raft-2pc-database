import transaction_pb2


class ResumeSerializer:

    def create(clusterId: int, serverId: int):
        resume_request = transaction_pb2.Resume()
        resume_request.clusterId = clusterId
        resume_request.serverId = serverId
        return resume_request.SerializeToString()
    
    def parse(resume_request_str: str):
        resume_request = transaction_pb2.Resume()
        resume_request.ParseFromString(resume_request_str)
        return resume_request