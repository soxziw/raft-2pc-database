import transaction_pb2


class CrossShardReqSerializer:
    
    def create(phase: int, senderClusterId: int, receiverClusterId: int, senderId: int, receiverId: int, amount: int, id: int):
        cross_shard_request = transaction_pb2.CrossShardReq()
        if phase == 0:
            cross_shard_request.phase = transaction_pb2.CrossShardPhaseType.PREPARE
        elif phase == 1:
            cross_shard_request.phase = transaction_pb2.CrossShardPhaseType.COMMIT
        else:
            cross_shard_request.phase = transaction_pb2.CrossShardPhaseType.ABORT

        cross_shard_request.id = id
        cross_shard_request.senderClusterId = senderClusterId
        cross_shard_request.receiverClusterId = receiverClusterId
        cross_shard_request.senderId = senderId
        cross_shard_request.receiverId = receiverId
        cross_shard_request.amount = amount
        return cross_shard_request.SerializeToString()
    

    def parse(cross_shard_request_str: str):
        cross_shard_request = transaction_pb2.CrossShardReq()
        cross_shard_request.ParseFromString(cross_shard_request_str)
        return cross_shard_request



