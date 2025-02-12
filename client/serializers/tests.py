import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from proto.intraShardRsp_pb2 import IntraShardResultType
from proto.crossShardReq_pb2 import CrossShardPhaseType
from proto.crossShardRsp_pb2 import CrossShardResultType
from proto.appendEntriesReq_pb2 import Entry
from serializers.IntraShardReq import IntraShardReqSerializer
from serializers.CrossShardReq import CrossShardReqSerializer
from serializers.IntraShardRsp import IntraShardRspSerialier
from serializers.CrossShardRsp import CrossShardRspSerializer
from serializers.Resume import ResumeSerializer
from serializers.Stop import StopSerializer
from serializers.printBalanceReq import printBalanceReqSerializer
from serializers.printBalanceRsp import printBalanceRspSerializer
from serializers.printDatastoreReq import printDatastoreReqSerializer
from serializers.printDatastoreRsp import printDatastoreRspSerializer



class Test2PCClient(unittest.TestCase):

    def test_intra_shard_req(self):
        intra_shard_request_str = IntraShardReqSerializer.to_str(clusterId=1, senderId=1, receiverId=2, amount=5, id=1)
        deserialized_intra_shard_req = IntraShardReqSerializer.parse(intra_shard_request_str)
        self.assertEqual(deserialized_intra_shard_req.clusterId, 1)
        self.assertEqual(deserialized_intra_shard_req.senderId, 1)
        self.assertEqual(deserialized_intra_shard_req.receiverId, 2)
        self.assertEqual(deserialized_intra_shard_req.amount, 5)

    def test_intra_shard_rsp(self):
        intra_shard_rsp_str = IntraShardRspSerialier.to_str(result=0, id=10)
        deserialized_intra_shard_rsp = IntraShardRspSerialier.parse(intra_shard_rsp_str)
        self.assertEqual(deserialized_intra_shard_rsp.result, IntraShardResultType.SUCCESS)
        self.assertEqual(deserialized_intra_shard_rsp.id, 10)

    def test_cross_shard_req(self):
        cross_shard_req_str = CrossShardReqSerializer.to_str(phase=0, senderClusterId = 1, receiverClusterId = 2, senderId=1, receiverId=1001, amount=5, id=1)
        deserialzed_cross_shard_req = CrossShardReqSerializer.parse(cross_shard_req_str)
        self.assertEqual(deserialzed_cross_shard_req.phase, CrossShardPhaseType.PREPARE)
        self.assertEqual(deserialzed_cross_shard_req.senderClusterId, 1)
        self.assertEqual(deserialzed_cross_shard_req.receiverClusterId, 2)
        self.assertEqual(deserialzed_cross_shard_req.senderId, 1)
        self.assertEqual(deserialzed_cross_shard_req.receiverId, 1001)
        self.assertEqual(deserialzed_cross_shard_req.amount, 5)

    def test_cross_shard_rsp(self):
        cross_shard_rsp_str = CrossShardRspSerializer.to_str(result=1, id=10)
        deserialized_cross_shard_rsp = CrossShardRspSerializer.parse(cross_shard_rsp_str)
        self.assertEqual(deserialized_cross_shard_rsp.result, CrossShardResultType.NO)
        self.assertEqual(deserialized_cross_shard_rsp.id, 10)

    def test_stop_req(self):
        stop_req_str = StopSerializer.to_str(clusterId=1, serverId=3)
        deserialized_stop_req = StopSerializer.parse(stop_req_str)
        self.assertEqual(deserialized_stop_req.clusterId, 1)
        self.assertEqual(deserialized_stop_req.serverId, 3)

    def test_resume_req(self):
        resume_req_str = ResumeSerializer.to_str(clusterId=1, serverId=3)
        deserialized_stop_req = ResumeSerializer.parse(resume_req_str)
        self.assertEqual(deserialized_stop_req.clusterId, 1)
        self.assertEqual(deserialized_stop_req.serverId, 3)

    def test_print_datastore_req(self):
        print_datastore_req_str = printDatastoreReqSerializer.to_str(clusterId=1, serverId=5)
        deserialized_print_datastore_req = printDatastoreReqSerializer.parse(print_datastore_req_str)
        self.assertEqual(deserialized_print_datastore_req.clusterId, 1)
        self.assertEqual(deserialized_print_datastore_req.serverId, 5)

    def test_print_datastore_rsp(self):
        entries = [Entry(term=1, index = 2,command = "election")]
        print_datastore_rsp_str = printDatastoreRspSerializer.to_str(clusterId=1, serverId=5, entries=entries)
        deserialized_print_datastore_rsp = printDatastoreRspSerializer.parse(print_datastore_rsp_str)
        print(deserialized_print_datastore_rsp)
        self.assertEqual(deserialized_print_datastore_rsp.clusterId, 1)
        self.assertEqual(deserialized_print_datastore_rsp.serverId, 5)
        self.assertEqual(deserialized_print_datastore_rsp.entries[0].term, 1)
        self.assertEqual(deserialized_print_datastore_rsp.entries[0].index, 2)
        self.assertEqual(deserialized_print_datastore_rsp.entries[0].command, "election")


    def test_print_balance_req(self):
        print_balance_req_str = printBalanceReqSerializer.to_str(clusterId=1, serverId=5, dataItemID = 3)
        deserialized_print_balance_req = printBalanceReqSerializer.parse(print_balance_req_str)
        self.assertEqual(deserialized_print_balance_req.clusterId, 1)
        self.assertEqual(deserialized_print_balance_req.serverId, 5)
        self.assertEqual(deserialized_print_balance_req.dataItemID, 3)

    def test_print_balance_rsp(self):
        print_balance_rsp_str = printBalanceRspSerializer.to_str(clusterId=1, serverId=5, dataItemID=3, balance=10)
        deserialized_print_balance_rsp = printBalanceRspSerializer.parse(print_balance_rsp_str)
        self.assertEqual(deserialized_print_balance_rsp.clusterId, 1)
        self.assertEqual(deserialized_print_balance_rsp.serverId, 5)
        self.assertEqual(deserialized_print_balance_rsp.dataItemID, 3)
        self.assertEqual(deserialized_print_balance_rsp.balance, 10)

    
        


if __name__ == '__main__':
    unittest.main()