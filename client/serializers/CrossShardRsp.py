import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from proto.crossShardRsp_pb2 import CrossShardRsp, CrossShardResultType
from proto.wrapperMessage_pb2 import WrapperMessage


class CrossShardRspSerializer:
    
    def to_str(result: int, id: int):
        cross_shard_response = CrossShardRsp()
        if result == 0:
            cross_shard_response.result = CrossShardResultType.YES
        elif result == 1:
            cross_shard_response.result = CrossShardResultType.NO
        else:
            cross_shard_response.result = CrossShardResultType.ACK

        cross_shard_response.id = id
        return WrapperMessage(crossShardRsp=cross_shard_response).SerializeToString()
    

    def parse(cross_shard_response_str: bytes):
        wrapper = WrapperMessage()
        wrapper.ParseFromString(cross_shard_response_str)
        if wrapper.HasField("crossShardRsp"):
            return wrapper.crossShardRsp

