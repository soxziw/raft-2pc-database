import Transaction_pb2


class IntraShardReqSerializer:
    def create(clusterId: int, senderId: int, receiverId: int, amount: int, id: int):
        intra_shard_request = Transaction_pb2.IntraShardReq()
        intra_shard_request.id = id
        intra_shard_request.clusterId = clusterId
        intra_shard_request.senderId = senderId
        intra_shard_request.receiverId = receiverId
        intra_shard_request.amount = amount
        return intra_shard_request.SerializeToString()
    
    def parse(intra_shard_request_str: str):
        intra_shard_request = Transaction_pb2.IntraShardReq()
        intra_shard_request.ParseFromString(intra_shard_request_str)
        return intra_shard_request



