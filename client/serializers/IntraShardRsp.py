import transaction_pb2


class IntraShardRspSerialier:

    def create(result: int, id: int):
        intra_shard_response = transaction_pb2.IntraShardRsp()
        if result == 0:
            intra_shard_response.result = transaction_pb2.IntraShardResultType.SUCCESS
        elif result == 1:
            intra_shard_response.result = transaction_pb2.IntraShardResultType.FAIL

        intra_shard_response.id = id
        return intra_shard_response.SerializeToString()
    
    def parse(intra_shard_response_json: str):
        intra_shard_response = transaction_pb2.IntraShardRsp()
        intra_shard_response.ParseFromString(intra_shard_response_json)
        return intra_shard_response

