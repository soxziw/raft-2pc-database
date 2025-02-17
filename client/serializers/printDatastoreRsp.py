import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from proto.printDatastoreRsp_pb2 import PrintDatastoreRsp
from proto.appendEntriesReq_pb2 import Entry
from proto.wrapperMessage_pb2 import WrapperMessage


class printDatastoreRspSerializer:

    def to_str(clusterId: int, serverId: int, entries: list[Entry]):
        print_datastore_rsp = PrintDatastoreRsp()
        print_datastore_rsp.clusterId = clusterId
        print_datastore_rsp.serverId = serverId
        print_datastore_rsp.entries.extend(entries)
        return WrapperMessage(printDatastoreRsp=print_datastore_rsp).SerializeToString()
    
    def parse(print_datastore_rsp_str: bytes):
        wrapper = WrapperMessage()
        wrapper.ParseFromString(print_datastore_rsp_str)
        if wrapper.HasField("printDatastoreRsp"):
            return wrapper.printDatastoreRsp