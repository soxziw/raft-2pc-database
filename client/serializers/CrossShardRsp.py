import Transaction_pb2


class CrossShardRspDeserializer:
    def parse(cross_shard_response_str: str):
        cross_shard_response = Transaction_pb2.CrossShardRsp()
        cross_shard_response.ParseFromString(cross_shard_response_str)
        return cross_shard_response

