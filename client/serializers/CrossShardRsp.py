import transaction_pb2


class CrossShardRspSerializer:
    
    def create(result: int, id: int):
        cross_shard_response = transaction_pb2.CrossShardRsp()
        if result == 0:
            cross_shard_response.result = transaction_pb2.CrossShardResultType.YES
        elif result == 1:
            cross_shard_response.result = transaction_pb2.CrossShardResultType.NO
        else:
            cross_shard_response.result = transaction_pb2.CrossShardResultType.ACK

        cross_shard_response.id = id
        return cross_shard_response.SerializeToString()
    

    def parse(cross_shard_response_str: str):
        cross_shard_response = transaction_pb2.CrossShardRsp()
        cross_shard_response.ParseFromString(cross_shard_response_str)
        return cross_shard_response

