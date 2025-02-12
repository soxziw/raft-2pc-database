import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from proto.intraShardReq_pb2 import IntraShardReq



class IntraShardReqSerializer:

    def to_str(clusterId: int, senderId: int, receiverId: int, amount: int, id: int):
        intra_shard_request = IntraShardReq()
        intra_shard_request.id = id
        intra_shard_request.clusterId = clusterId
        intra_shard_request.senderId = senderId
        intra_shard_request.receiverId = receiverId
        intra_shard_request.amount = amount
        return intra_shard_request.SerializeToString()
    
    def parse(intra_shard_request_str: bytes):
        intra_shard_request = IntraShardReq()
        intra_shard_request.ParseFromString(intra_shard_request_str)
        return intra_shard_request



