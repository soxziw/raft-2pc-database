import socket
import utils
from manager import CrossShardTransactionManager
import json
from serializers.IntraShardReq import IntraShardReqSerializer
from serializers.IntraShardRsp import IntraShardRspSerializer
from proto.intraShardRsp_pb2 import IntraShardResultType
from serializers.printBalanceReq import printBalanceReqSerializer
from serializers.printBalanceRsp import printBalanceRspSerializer
from serializers.Stop import StopSerializer
from serializers.Resume import ResumeSerializer
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))


with open('../config.json') as f:
    CONFIG = json.load(f)


class TransactionHandler:
    routing_service_ip_port = (CONFIG['ROUTING_SERVICE']['IP'],CONFIG['ROUTING_SERVICE']['PORT'])
    num_cluster = len(CONFIG['SERVERS'])
    num_server_per_cluster = len(CONFIG['SERVERS'][0]) if isinstance(CONFIG.get('SERVERS'), list) and CONFIG['SERVERS'] else 0
    server_ip_port_list = [[0] * 3 for _ in range(num_cluster)]
    for i in range(num_cluster):
        for j in range(num_server_per_cluster):
            server_ip_port_list[i][j] = (CONFIG['SERVERS'][i][j]['IP'],CONFIG['SERVERS'][i][j]['PORT'])
    # print(server_ip_port_list)
    

    @classmethod
    def transfer(cls, sender_id: int, recipient_id: int, amount: int):
        """Handling a new transfer transaction"""
        sender_cluser_id = cls.get_cluster_id_for_user(sender_id)
        recipient_cluser_id = cls.get_cluster_id_for_user(recipient_id)
        if sender_cluser_id == recipient_cluser_id:
            cls.send_intra_shard_transaction(sender_cluser_id, sender_id, recipient_id, amount)
        else:
            cls.send_cross_shard_transaction(sender_cluser_id, recipient_cluser_id, sender_id, recipient_id, amount)

    
    @classmethod
    def send_intra_shard_transaction(cls, cluser_id: int, sender_id: int, recipient_id: int, amount: int):
        """Sending a intra-shard transaction request to a designated server within the relevant cluster """
        message = IntraShardReqSerializer.to_str(clusterId=cluser_id, senderId=sender_id, receiverId=recipient_id, amount=amount, id=1)
        ip, port = cls.routing_service_ip_port
        response = utils.send_message(ip, port, message)
        intra_shard_response = IntraShardRspSerializer.parse(response)
        if intra_shard_response.result == IntraShardResultType.SUCCESS:
            print(f"Transaction SUCCESS: user {sender_id} has transferred ${amount} to {recipient_id}")
        else:
            print(f"Transaction FAILED")





    @classmethod
    def send_cross_shard_transaction(cls, sender_cluser_id: int, recipient_cluser_id: int, sender_id: int, recipient_id: int, amount: int):
        """Sending a cross-shard transaction request to a designated server in each of the relevant clusters."""
        CrossShardTransactionManager.send_prepare_message()

    @classmethod
    def get_cluster_id_for_user(cls, user_id: int) -> int:
        """return the clusterid of the cluster that holds the data item for user"""
        return (user_id - 1) // 1000 + 1

    @classmethod
    def get_cluster_id_for_server(cls, server_id: int) -> int:
        """return the clusterid of the cluster that hosts the server"""
        return (server_id - 1) // 3 + 1
        

    @classmethod
    def get_balance(cls, user_id: int) -> list[int]:
        """Read the balance of a given user from the database and prints the balance on all server"""
        cluster_id = cls.get_cluster_id_for_user(user_id)
        balance_res = []
        for i in range(cls.num_server_per_cluster):
            ip, port =  cls.server_ip_port_list[cluster_id - 1][i]
            server_id = cls.num_server_per_cluster * (cluster_id - 1) + i + 1
            message = printBalanceReqSerializer.to_str(clusterId=cluster_id,serverId=server_id , dataItemID=user_id)
            response = utils.send_message(ip, port, message)
            print_balance_response = printBalanceRspSerializer.parse(response)
            balance_res.append((print_balance_response.clusterId, print_balance_response.serverId, print_balance_response.balance))
        return balance_res

        

    @classmethod
    def get_data_store(cls) -> list:
        """Return the set of committed transactions on each server."""
        pass
    
    @classmethod
    def stop(cls, server_id: int):
        """Stop the designated server"""
        cluster_id = cls.get_cluster_id_for_server(server_id)
        message = StopSerializer.to_str(cluster_id, server_id)
        ip, port = cls.server_ip_port_list[cluster_id - 1][server_id - cluster_id * cls.num_server_per_cluster + 2]
        utils.send_message(ip, port, message)
        print(f"Server {server_id} stop SUCCEED")
        

    @classmethod
    def resume(cls, server_id: int):
        """Resume the designated server"""
        cluster_id = cls.get_cluster_id_for_server(server_id)
        message = ResumeSerializer.to_str(cluster_id, server_id)
        ip, port = cls.server_ip_port_list[cluster_id - 1][server_id - 1]
        utils.send_message(ip, port, message)
        print(f"Server {server_id} resume SUCCEED")

    @classmethod
    def get_performance_metrics(cls):
        pass
