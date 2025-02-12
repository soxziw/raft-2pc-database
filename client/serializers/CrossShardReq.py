import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from proto.crossShardReq_pb2 import CrossShardReq, CrossShardPhaseType


class CrossShardReqSerializer:
    
    def to_str(phase: int, senderClusterId: int, receiverClusterId: int, senderId: int, receiverId: int, amount: int, id: int):
        cross_shard_request = CrossShardReq()
        if phase == 0:
            cross_shard_request.phase = CrossShardPhaseType.PREPARE
        elif phase == 1:
            cross_shard_request.phase = CrossShardPhaseType.COMMIT
        else:
            cross_shard_request.phase = CrossShardPhaseType.ABORT

        cross_shard_request.id = id
        cross_shard_request.senderClusterId = senderClusterId
        cross_shard_request.receiverClusterId = receiverClusterId
        cross_shard_request.senderId = senderId
        cross_shard_request.receiverId = receiverId
        cross_shard_request.amount = amount
        return cross_shard_request.SerializeToString()
    

    def parse(cross_shard_request_str: bytes):
        cross_shard_request = CrossShardReq()
        cross_shard_request.ParseFromString(cross_shard_request_str)
        return cross_shard_request



