import unittest
import transaction_pb2
from serializers.IntraShardReq import IntraShardReqSerializer
from serializers.CrossShardReq import CrossShardReqSerializer
from serializers.IntraShardRsp import IntraShardRspSerialier
from serializers.CrossShardRsp import CrossShardRspSerializer
from serializers.Resume import ResumeSerializer
from serializers.Stop import StopSerializer



class Test2PCClient(unittest.TestCase):

    def test_intra_shard_req(self):
        intra_shard_request_str = IntraShardReqSerializer.create(clusterId=1, senderId=1, receiverId=2, amount=5, id=1)
        deserialized_intra_shard_req = IntraShardReqSerializer.parse(intra_shard_request_str)
        self.assertEqual(deserialized_intra_shard_req.clusterId, 1)
        self.assertEqual(deserialized_intra_shard_req.senderId, 1)
        self.assertEqual(deserialized_intra_shard_req.receiverId, 2)
        self.assertEqual(deserialized_intra_shard_req.amount, 5)

    def test_intra_shard_rsp(self):
        intra_shard_rsp_str = IntraShardRspSerialier.create(result=0, id=10)
        deserialized_intra_shard_rsp = IntraShardRspSerialier.parse(intra_shard_rsp_str)
        self.assertEqual(deserialized_intra_shard_rsp.result, transaction_pb2.IntraShardResultType.SUCCESS)
        self.assertEqual(deserialized_intra_shard_rsp.id, 10)

    def test_cross_shard_req(self):
        cross_shard_req_str = CrossShardReqSerializer.create(phase=0, senderClusterId = 1, receiverClusterId = 2, senderId=1, receiverId=1001, amount=5, id=1)
        deserialzed_cross_shard_req = CrossShardReqSerializer.parse(cross_shard_req_str)
        self.assertEqual(deserialzed_cross_shard_req.phase, transaction_pb2.CrossShardPhaseType.PREPARE)
        self.assertEqual(deserialzed_cross_shard_req.senderClusterId, 1)
        self.assertEqual(deserialzed_cross_shard_req.receiverClusterId, 2)
        self.assertEqual(deserialzed_cross_shard_req.senderId, 1)
        self.assertEqual(deserialzed_cross_shard_req.receiverId, 1001)
        self.assertEqual(deserialzed_cross_shard_req.amount, 5)

    def test_cross_shard_rsp(self):
        cross_shard_rsp_str = CrossShardRspSerializer.create(result=1, id=10)
        deserialized_cross_shard_rsp = CrossShardRspSerializer.parse(cross_shard_rsp_str)
        self.assertEqual(deserialized_cross_shard_rsp.result, transaction_pb2.CrossShardResultType.NO)
        self.assertEqual(deserialized_cross_shard_rsp.id, 10)

    def test_stop_req(self):
        stop_req_str = StopSerializer.create(clusterId=1, serverId=3)
        deserialized_stop_req = StopSerializer.parse(stop_req_str)
        self.assertEqual(deserialized_stop_req.clusterId, 1)
        self.assertEqual(deserialized_stop_req.serverId, 3)

    def test_resume_req(self):
        resume_req_str = ResumeSerializer.create(clusterId=1, serverId=3)
        deserialized_stop_req = ResumeSerializer.parse(resume_req_str)
        self.assertEqual(deserialized_stop_req.clusterId, 1)
        self.assertEqual(deserialized_stop_req.serverId, 3)
        


if __name__ == '__main__':
    unittest.main()