import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from proto.printBalanceReq_pb2 import PrintBalanceReq

class printBalanceReqSerializer:

    def to_str(clusterId: int, serverId: int, dataItemID: int):
        print_balance_req = PrintBalanceReq()
        print_balance_req.clusterId = clusterId
        print_balance_req.serverId = serverId
        print_balance_req.dataItemID = dataItemID
        return print_balance_req.SerializeToString()
    
    def parse(print_balance_req_str: bytes):
        print_balance_req = PrintBalanceReq()
        print_balance_req.ParseFromString(print_balance_req_str)
        return print_balance_req