import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from proto.resume_pb2 import Resume


class ResumeSerializer:

    def to_str(clusterId: int, serverId: int):
        resume_request = Resume()
        resume_request.clusterId = clusterId
        resume_request.serverId = serverId
        return resume_request.SerializeToString()
    
    def parse(resume_request_str: bytes):
        resume_request = Resume()
        resume_request.ParseFromString(resume_request_str)
        return resume_request