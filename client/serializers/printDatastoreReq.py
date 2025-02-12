import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from proto.printDatastoreReq_pb2 import PrintDatastoreReq

class printDatastoreReqSerializer:

    def to_str(clusterId: int, serverId: int):
        print_datastore_req = PrintDatastoreReq()
        print_datastore_req.clusterId = clusterId
        print_datastore_req.serverId = serverId
        return print_datastore_req.SerializeToString()
    
    def parse(print_datastore_req_str: bytes):
        print_datastore_req = PrintDatastoreReq()
        print_datastore_req.ParseFromString(print_datastore_req_str)
        return print_datastore_req