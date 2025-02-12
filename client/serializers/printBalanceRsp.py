import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from proto.printBalanceRsp_pb2 import PrintBalanceRsp

class printBalanceRspSerializer:

    def to_str(clusterId: int, serverId: int, dataItemID: int, balance: int):
        print_balance_rsp = PrintBalanceRsp()
        print_balance_rsp.clusterId = clusterId
        print_balance_rsp.serverId = serverId
        print_balance_rsp.dataItemID = dataItemID
        print_balance_rsp.balance = balance
        return print_balance_rsp.SerializeToString()
    
    def parse(print_balance_rsp_str: bytes):
        print_balance_rsp = PrintBalanceRsp()
        print_balance_rsp.ParseFromString(print_balance_rsp_str)
        return print_balance_rsp