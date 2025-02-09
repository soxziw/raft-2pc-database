import Transaction_pb2


class IntraShardRspDeserialier:
    def parse(intra_shard_response_json: str):
        intra_shard_response = Transaction_pb2.IntraShardRsp()
        intra_shard_response.ParseFromString(intra_shard_response_json)
        return intra_shard_response

