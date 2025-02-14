import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from proto.printDatastoreReq_pb2 import PrintDatastoreReq
from proto.wrapperMessage_pb2 import WrapperMessage


class printDatastoreReqSerializer:

    def to_str(clusterId: int, serverId: int):
        print_datastore_req = PrintDatastoreReq()
        print_datastore_req.clusterId = clusterId
        print_datastore_req.serverId = serverId
        return WrapperMessage(printDatastoreReq=print_datastore_req).SerializeToString()
    
    def parse(print_datastore_req_str: bytes):
        wrapper = WrapperMessage()
        wrapper.ParseFromString(print_datastore_req_str)
        if wrapper.HasField("printDatastoreReq"):
            return wrapper.printDatastoreReq