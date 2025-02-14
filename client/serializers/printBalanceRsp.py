import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from proto.printBalanceRsp_pb2 import PrintBalanceRsp
from proto.wrapperMessage_pb2 import WrapperMessage


class printBalanceRspSerializer:

    def to_str(clusterId: int, serverId: int, dataItemID: int, balance: int):
        print_balance_rsp = PrintBalanceRsp()
        print_balance_rsp.clusterId = clusterId
        print_balance_rsp.serverId = serverId
        print_balance_rsp.dataItemID = dataItemID
        print_balance_rsp.balance = balance
        return WrapperMessage(printBalanceRsp=print_balance_rsp).SerializeToString()
    
    def parse(print_balance_rsp_str: bytes):
        wrapper = WrapperMessage()
        wrapper.ParseFromString(print_balance_rsp_str)
        if wrapper.HasField("printBalanceRsp"):
            return wrapper.printBalanceRsp