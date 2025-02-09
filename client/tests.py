import unittest
from serializers.IntraShardReq import IntraShardReqSerializer
from serializers.CrossShardReq import CrossShardReqSerializer
import Transaction_pb2


class Test2PCClient(unittest.TestCase):
    def test_serialize_intra_shard_request(self):
        intra_shard_request_str = IntraShardReqSerializer.create(clusterId=1, senderId=1, receiverId=2, amount=5, id=1)
        intra_shard_request = IntraShardReqSerializer.parse(intra_shard_request_str)
        self.assertEqual(intra_shard_request.clusterId, 1)
        self.assertEqual(intra_shard_request.senderId, 1)
        self.assertEqual(intra_shard_request.receiverId, 2)
        self.assertEqual(intra_shard_request.amount, 5)

    def test_serialize_cross_shard_request(self):
        cross_shard_request_str = CrossShardReqSerializer.create(phase=0, senderClusterId = 1, receiverClusterId = 2, senderId=1, receiverId=1001, amount=5, id=1)
        cross_shard_request = CrossShardReqSerializer.parse(cross_shard_request_str)
        self.assertEqual(cross_shard_request.phase, Transaction_pb2.CrossShardPhaseType.PREPARE)
        self.assertEqual(cross_shard_request.senderClusterId, 1)
        self.assertEqual(cross_shard_request.receiverClusterId, 2)
        self.assertEqual(cross_shard_request.senderId, 1)
        self.assertEqual(cross_shard_request.receiverId, 1001)
        self.assertEqual(cross_shard_request.amount, 5)

    


    def test_intra_shard_transaction(self):
        pass

    def test_cross_shard_transaction(self):
        pass

if __name__ == '__main__':
    unittest.main()