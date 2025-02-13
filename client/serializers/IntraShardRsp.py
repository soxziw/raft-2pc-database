import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from proto.intraShardRsp_pb2 import IntraShardRsp, IntraShardResultType
from proto.wrapperMessage_pb2 import WrapperMessage


class IntraShardRspSerializer:

    def to_str(result: int, id: int):
        intra_shard_response = IntraShardRsp()
        if result == 0:
            intra_shard_response.result = IntraShardResultType.SUCCESS
        elif result == 1:
            intra_shard_response.result = IntraShardResultType.FAIL

        intra_shard_response.id = id
        return WrapperMessage(intraShardRsp=intra_shard_response).SerializeToString()
    
    def parse(intra_shard_response_str: bytes):
        wrapper = WrapperMessage()
        wrapper.ParseFromString(intra_shard_response_str)
        if wrapper.HasField("intraShardRsp"):
            return wrapper.intraShardRsp

