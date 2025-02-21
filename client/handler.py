import utils
from serializers.IntraShardReq import IntraShardReqSerializer
from serializers.CrossShardReq import CrossShardReqSerializer
from serializers.printBalanceReq import printBalanceReqSerializer
from serializers.printBalanceRsp import printBalanceRspSerializer
from serializers.printDatastoreReq import printDatastoreReqSerializer
from serializers.printDatastoreRsp import printDatastoreRspSerializer
from serializers.Stop import StopSerializer
from serializers.Resume import ResumeSerializer
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
from config import LocalConfig


class TransactionHandler:

    @classmethod
    def transfer(cls, sender_id: int, recipient_id: int, amount: int):
        """Handling a new transfer transaction"""
        sender_cluser_id = LocalConfig.get_cluster_id_for_user(sender_id)
        recipient_cluser_id = LocalConfig.get_cluster_id_for_user(recipient_id)
        if sender_cluser_id == recipient_cluser_id:
            cls.send_intra_shard_transaction_to_routingservice(sender_cluser_id, sender_id, recipient_id, amount)
        else:
            cls.send_cross_shard_transaction_to_routingservice(sender_cluser_id, recipient_cluser_id, sender_id, recipient_id, amount)

    
    @classmethod
    def send_intra_shard_transaction_to_routingservice(cls, cluser_id: int, sender_id: int, recipient_id: int, amount: int):
        """Sending a intra-shard transaction request to the routing service"""

        message = IntraShardReqSerializer.to_str(clusterId=cluser_id, senderId=sender_id, receiverId=recipient_id, amount=amount, id=1)
        ip, port = LocalConfig.routing_service_ip_port
        
        print("Sending intra-shard transaction request to routing service...")

        utils.send_message(ip, port, message, with_response=False)
        # intra_shard_response = IntraShardRspSerializer.parse(response)
        # if intra_shard_response.result == IntraShardResultType.SUCCESS:
        #     print(f"Transaction SUCCESS: user {sender_id} has transferred ${amount} to {recipient_id}")
        # else:
        #     print(f"Transaction FAILED")





    @classmethod
    def send_cross_shard_transaction_to_routingservice(cls, sender_cluser_id: int, recipient_cluser_id: int, sender_id: int, recipient_id: int, amount: int):
        """Sending a cross-shard transaction request to the routing service"""
        message = CrossShardReqSerializer.to_str(0, sender_cluser_id, recipient_cluser_id, sender_id, recipient_id, amount, 0)
        ip, port = LocalConfig.routing_service_ip_port
        
        print("Sending cross-shard transaction request to routing service...")

        utils.send_message(ip, port, message, with_response=False)
        # cross_shard_response = CrossShardRspSerializer.parse(response)
        # if cross_shard_response.result == CrossShardResultType.SUCCESS:
        #     print(f"Transaction SUCCESS: user {sender_id} has transferred ${amount} to {recipient_id}")
        # else:
        #     print(f"Transaction FAILED")
        

    @classmethod
    def get_balance(cls, user_id: int) -> list[int]:
        """Read the balance of a given user from the database and prints the balance on all server"""
        cluster_id = LocalConfig.get_cluster_id_for_user(user_id)
        balance_res = []
        for i in range(LocalConfig.num_server_per_cluster):
            ip, port =  LocalConfig.server_ip_port_list[cluster_id][i]
            server_id = LocalConfig.num_server_per_cluster * cluster_id + i
            message = printBalanceReqSerializer.to_str(clusterId=cluster_id,serverId=server_id , dataItemID=user_id)
            response = utils.send_message(ip, port, message, with_response=True)
            print_balance_response = printBalanceRspSerializer.parse(response)
            balance_res.append((print_balance_response.clusterId, print_balance_response.serverId, print_balance_response.balance))
        return balance_res

        

    @classmethod
    def get_data_store(cls) -> list:
        """Return the set of committed transactions on each server."""
        datastore_res = []
        for i in range(LocalConfig.num_cluster):
            for j in range(LocalConfig.num_server_per_cluster):
                ip, port = LocalConfig.server_ip_port_list[i][j]
                cluster_id = i
                server_id = LocalConfig.server_index_to_id(i, j)
                message = printDatastoreReqSerializer.to_str(cluster_id, server_id)
                response = utils.send_message(ip, port, message, with_response=True)
                print_datastore_response = printDatastoreRspSerializer.parse(response)
                for entry in print_datastore_response.entries:
                    datastore_res.append((cluster_id, server_id, entry.term, entry.index, entry.command))
        return datastore_res
    
    @classmethod
    def stop(cls, server_id: int):
        """Stop the designated server"""
        cluster_id = LocalConfig.get_cluster_id_for_server(server_id)
        message = StopSerializer.to_str(cluster_id, server_id)
        server_index = LocalConfig.server_id_to_index(server_id)
        ip, port = LocalConfig.server_ip_port_list[cluster_id][server_index]
        utils.send_message(ip, port, message, with_response=False)
        print(f"Server {server_id} stops SUCCEED")
        

    @classmethod
    def resume(cls, server_id: int):
        """Resume the designated server"""
        cluster_id = LocalConfig.get_cluster_id_for_server(server_id)
        message = ResumeSerializer.to_str(cluster_id, server_id)
        server_index = LocalConfig.server_id_to_index(server_id)
        ip, port = LocalConfig.server_ip_port_list[cluster_id][server_index]
        utils.send_message(ip, port, message, with_response=False)
        print(f"Server {server_id} resumes SUCCEED")

    @classmethod
    def get_performance_metrics(cls):
        pass
