import Transaction_pb2


class CrossShardReqSerializer:
    def create(phase: int, senderClusterId: int, receiverClusterId: int, senderId: int, receiverId: int, amount: int, id: int):
        cross_shard_request = Transaction_pb2.CrossShardReq()
        if phase == 0:
            cross_shard_request.phase = Transaction_pb2.CrossShardPhaseType.PREPARE
        elif phase == 1:
            cross_shard_request.phase = Transaction_pb2.CrossShardPhaseType.COMMIT
        else:
            cross_shard_request.phase = Transaction_pb2.CrossShardPhaseType.ABORT

        cross_shard_request.id = id
        cross_shard_request.senderClusterId = senderClusterId
        cross_shard_request.receiverClusterId = receiverClusterId
        cross_shard_request.senderId = senderId
        cross_shard_request.receiverId = receiverId
        cross_shard_request.amount = amount
        return cross_shard_request.SerializeToString()
    
    def parse(cross_shard_response_str: str):
        intra_shard_response = Transaction_pb2.CrossShardReq()
        intra_shard_response.ParseFromString(cross_shard_response_str)
        return intra_shard_response



