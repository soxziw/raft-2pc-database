
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
import unittest

import utils
from serializers.IntraShardReq import IntraShardReqSerializer
from serializers.IntraShardRsp import IntraShardRspSerializer
from serializers.CrossShardReq import CrossShardReqSerializer
from serializers.CrossShardRsp import CrossShardRspSerializer
from serializers.printBalanceReq import printBalanceReqSerializer
from serializers.printBalanceRsp import printBalanceRspSerializer
from serializers.printDatastoreReq import printDatastoreReqSerializer
from serializers.printDatastoreRsp import printDatastoreRspSerializer
from serializers.Stop import StopSerializer
from serializers.Resume import ResumeSerializer
from proto.intraShardRsp_pb2 import IntraShardResultType
from proto.crossShardRsp_pb2 import CrossShardResultType
import time
from config import LocalConfig


class TransactionHandler:

    @classmethod
    async def transfer(cls, sender_id: int, recipient_id: int, amount: int):
        """Handling a new transfer transaction"""
        sender_cluser_id = LocalConfig.get_cluster_id_for_user(sender_id)
        recipient_cluser_id = LocalConfig.get_cluster_id_for_user(recipient_id)
        start = time.time()
        if sender_cluser_id == recipient_cluser_id:
            await cls.send_intra_shard_transaction_to_routingservice(sender_cluser_id, sender_id, recipient_id, amount)
        else:
            await cls.send_cross_shard_transaction_to_routingservice(sender_cluser_id, recipient_cluser_id, sender_id, recipient_id, amount)
        end = time.time()
        return end - start

    
    @classmethod
    async def send_intra_shard_transaction_to_routingservice(cls, cluster_id: int, sender_id: int, recipient_id: int, amount: int):
        """Sending a intra-shard transaction request to the routing service"""

        message = IntraShardReqSerializer.to_str(clusterId=cluster_id, senderId=sender_id, receiverId=recipient_id, amount=amount, id=1)

        ip, port = LocalConfig.routing_service_ip_port
        print(f"Sending intra-shard transaction [clusterId={cluster_id}] request to routing service {ip}:{port}...")

        try:
            response = await utils.send_message_async(ip, port, message, with_response=True)
            intra_shard_response = IntraShardRspSerializer.parse(response)
            if intra_shard_response.result == IntraShardResultType.SUCCESS:
                print(f"\033[32mTransaction SUCCEED: user {sender_id} has transferred ${amount} to {recipient_id}\033[0m")
            else:
                print(f"\033[31mTransaction FAILED: user {sender_id} fails to transfer ${amount} to {recipient_id}\033[0m")
        except TimeoutError:
            print(f"\033[31mTransaction FAILED: user {sender_id} fails to transfer ${amount} to {recipient_id}\033[0m")
            





    @classmethod
    async def send_cross_shard_transaction_to_routingservice(cls, sender_cluser_id: int, recipient_cluser_id: int, sender_id: int, recipient_id: int, amount: int):
        """Sending a cross-shard transaction request to the routing service"""
        message = CrossShardReqSerializer.to_str(0, sender_cluser_id, recipient_cluser_id, sender_id, recipient_id, amount, 0)
        ip, port = LocalConfig.routing_service_ip_port
        
        print(f"Sending cross-shard transaction request[senderClusterId={sender_cluser_id}, receiverClusterId={recipient_cluser_id}] to routing service {ip}:{port}...")

        cross_shard_response = await utils.send_message_async(ip, port, message, with_response=True)

        if cross_shard_response and cross_shard_response.decode() == "Transaction SUCCEED":
            print(f"\033[32mTransaction SUCCEED: user {sender_id} has transferred ${amount} to {recipient_id}\033[0m")
        else:
            print(f"\033[31mTransaction FAILED: user {sender_id} fails to transfer ${amount} to {recipient_id}\033[0m")
        

    @classmethod
    def get_balance(cls, user_id: int) -> list[int]:
        """Read the balance of a given user from the database and prints the balance on all server"""
        cluster_id = LocalConfig.get_cluster_id_for_user(user_id)
        balance_res = []
        for i in range(LocalConfig.num_server_per_cluster):
            ip, port =  LocalConfig.server_ip_port_list[cluster_id][i]
            server_id = LocalConfig.num_server_per_cluster * cluster_id + i
            print(f"Retrieving balance for {user_id} from cluster {cluster_id} and server {server_id}...")
            message = printBalanceReqSerializer.to_str(clusterId=cluster_id,serverId=server_id , dataItemID=user_id)
            response = utils.send_message(ip, port, message, with_response=True, return_timeout=True)
            balance = utils.TIMEOUT_ERROR if response == utils.TIMEOUT_ERROR else printBalanceRspSerializer.parse(response).balance
            balance_res.append((cluster_id, server_id, balance))
        return balance_res

        

    @classmethod
    def get_data_store(cls) -> list:
        """Return the set of committed transactions on each server."""
        datastore_res = []
        for i in range(LocalConfig.num_cluster):
            for j in range(LocalConfig.num_server_per_cluster):
                datastore_per_server = []
                ip, port = LocalConfig.server_ip_port_list[i][j]
                cluster_id = i
                server_id = LocalConfig.server_index_to_id(i, j)
                print(f"Retrieving datastore for from cluster {cluster_id} and server {server_id}...")
                message = printDatastoreReqSerializer.to_str(clusterId=cluster_id, serverId=server_id)
                print(printDatastoreReqSerializer.parse(message))
                response = utils.send_message(ip, port, message, with_response=True, return_timeout=True)
                if response == utils.TIMEOUT_ERROR:
                    datastore_res.append(utils.TIMEOUT_ERROR)
                else:
                    entries = printDatastoreRspSerializer.parse(response).entries
                    for entry in entries:
                        datastore_per_server.append((cluster_id, server_id, entry.term, entry.index, entry.command))
                    datastore_res.append(datastore_per_server)
        return datastore_res
    
    @classmethod
    def stop(cls, server_id: int):
        """Stop the designated server"""
        cluster_id = LocalConfig.get_cluster_id_for_server(server_id)
        print(f"Stoping server {server_id} from cluster {cluster_id}...")
        message = StopSerializer.to_str(cluster_id, server_id)
        server_index = LocalConfig.server_id_to_index(server_id)
        ip, port = LocalConfig.server_ip_port_list[cluster_id][server_index]
        print(f"Sending request to {ip}:{port}...")
        utils.send_message(ip, port, message, with_response=False)
        print(f"Server {server_id} stops SUCCEED")
        

    @classmethod
    def resume(cls, server_id: int):
        """Resume the designated server"""
        cluster_id = LocalConfig.get_cluster_id_for_server(server_id)
        print(f"Resuming server {server_id} from cluster {cluster_id}...")
        message = ResumeSerializer.to_str(cluster_id, server_id)
        server_index = LocalConfig.server_id_to_index(server_id)
        ip, port = LocalConfig.server_ip_port_list[cluster_id][server_index]
        print(f"Sending request to {ip}:{port}...")
        utils.send_message(ip, port, message, with_response=False)
        print(f"Server {server_id} resumes SUCCEED")
