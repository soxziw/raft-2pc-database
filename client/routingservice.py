import os, sys, json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
import utils 
from proto.wrapperMessage_pb2 import WrapperMessage
from proto.intraShardRsp_pb2 import IntraShardResultType
from proto.crossShardRsp_pb2 import CrossShardResultType
from serializers.IntraShardRsp import IntraShardRspSerializer
from serializers.CrossShardRsp import CrossShardRspSerializer
from serializers.CrossShardReq import CrossShardReqSerializer
from config import LocalConfig
import asyncio



class RoutingService:
    def __init__(self,  hostname: str, port: int):
        self.hostname = hostname
        self.port = port
        self.num_cluster = LocalConfig.num_cluster
        # store the leader of each cluster known via heartbeat
        self.leader_per_cluster = [0] * self.num_cluster
        # track the number of "YES" in 2PC Commit/Abort phase
        self.num_reply_for_2PC = []
        # store the request in queue when no leader is elected for that cluster
        self.transaction_request = [[] for _ in range(self.num_cluster)]


    def start(self):
        """Start the routing service asynchronously."""
        asyncio.create_task(self.server_thread())
        # threading.Thread(target=self.server_thread, daemon=True).start()

    # def server_thread(self):
    #     """Using the TCP/UDP as the message passing protocal"""
    #     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    #         server.bind((self.hostname, self.port))
    #         server.setblocking(False)
    #         server.listen()
    #         print(f"Routing service {self.client_id} listening on port {self.port}...")
    #         while True:
    #             conn, addr = server.accept()
    #             # print(f"Accepted connection from {addr}")
    #             with conn:
    #                 request_message = conn.recv(utils.BUFFER_SIZE)
    #                 await self.handle_request(conn, request_message)
    #             # close the connection
    #             conn.close()


    
    async def server_thread(self):
        """Asynchronous and Non-Blocking TCP server for handling requests."""
        server = await asyncio.start_server(
            self.handle_connection, self.hostname, self.port
        )

        addr = server.sockets[0].getsockname()
        print(f"Routing service {self.client_id} listening on {addr}...")

        async with server:
            await server.serve_forever()


    async def handle_connection(self, reader, writer):
        """Handle incoming connection from other clients"""
        addr = writer.get_extra_info("peername")
        print(f"Accepted connection from {addr}")

        try:
            request_message = await reader.read(utils.BUFFER_SIZE)  # Adjust buffer size as needed
            await self.handle_request(writer, request_message)
        finally:
            writer.close()
            await writer.wait_closed()


    async def handle_request(self, writer, request_message: bytes):
        """Placeholder for handling incoming requests."""
        wrapper = WrapperMessage()
        wrapper.ParseFromString(request_message)
        if wrapper.HasField("appendEntriesReq"):
            append_entries_req = wrapper.appendEntriesReq
            server_id = append_entries_req.leaderId
            cluster_id = LocalConfig.get_cluster_id_for_server(server_id)
            # new leader is elected, update leader table
            self.leader_per_cluster[cluster_id] = server_id
            # execute all the pending request for that cluster
            pending_requests= self.transaction_request[cluster_id]
            if len(pending_requests) > 0:
                while pending_requests:
                    request = pending_requests.pop(0)
                    wrapper.ParseFromString(request)
                    if wrapper.HasField("intraShardReq"):
                        await self.redirect_intra_shard_request_to_server(request)
                    elif wrapper.HasField("crossShardReq"):
                        await self.redirect_cross_shard_request_to_server(request, cluster_id)

        elif wrapper.HasField("requestVoteReq"):
            request_vote_req = wrapper.requestVoteReq
            server_id = request_vote_req.candidateId
            cluster_id = LocalConfig.get_cluster_id_for_server(server_id)
            # elections are on going, set leader to -1
            # server_id = [0,8]
            self.leader_per_cluster[cluster_id] = -1

        elif wrapper.HasField("intraShardReq"):
            """Redirect an intra-shard transaction request to a designated server within the relevant cluster """
            intra_shard_req = wrapper.intraShardReq
            if self.leader_per_cluster[intra_shard_req.clusterId] == -1:
                # no leader, put the request in the queue
                self.transaction_request[intra_shard_req.clusterId].append(request_message)
                return
            else:
                await self.redirect_intra_shard_request_to_server(request_message)

        elif wrapper.HasField("crossShardReq"):
            """Redirect a cross-shard transaction request to a designated server in each of the relevant clusters."""
            cross_shard_req = wrapper.cross_shard_req
            # increment id for the cross-shard-request
            cur = len(self.num_reply_for_2PC)
            self.num_reply_for_2PC.append(0)
            cur += 1
            message_with_id = CrossShardReqSerializer.to_str(utils.CrossShardPhaseType.PREPARE, cross_shard_req.senderClusterId, cross_shard_req.receiverClusterId,\
                                                 cross_shard_req.senderId, cross_shard_req.receiverId, cross_shard_req.amount, cur)
        
            if self.leader_per_cluster[cross_shard_req.senderClusterId] == -1:
                # no leader, put the request in the queue
                self.transaction_request[cross_shard_req.senderClusterId].append(message_with_id)
            else:
                await self.redirect_cross_shard_request_to_server(message_with_id, cross_shard_req.senderClusterId)

            if self.leader_per_cluster[cross_shard_req.receiverClusterId] == -1:
                # no leader, put the request in the queue
                self.transaction_request[cross_shard_req.receiverClusterId].append(message_with_id)
            else:
                await self.redirect_cross_shard_request_to_server(message_with_id, cross_shard_req.receiverClusterId)
                
            

    async def redirect_intra_shard_request_to_server(self, request_message: bytes):
        wrapper = WrapperMessage()
        wrapper.ParseFromString(request_message)
        intra_shard_req = wrapper.intraShardReq
        leader_id = self.leader_per_cluster[intra_shard_req.clusterId]
        server_index = LocalConfig.server_id_to_index(leader_id)
        ip, port = LocalConfig.server_ip_port_list[intra_shard_req.clusterId][server_index]
        
        print(f"Routingservice redirecting intra-shard transaction request[user {intra_shard_req.senderId} transfers to user {intra_shard_req.receiverId}\
               ${intra_shard_req.amount}] to cluser {intra_shard_req.cluster_id}, server {leader_id}...")
        response = await utils.send_message_async(ip, port, request_message, with_response=True)

        intra_shard_response = IntraShardRspSerializer.parse(response)
        if intra_shard_response.result == IntraShardResultType.SUCCESS:
            print(f"Transaction SUCCESS: user {intra_shard_req.senderId} has transferred ${intra_shard_req.amount} to {intra_shard_req.receiverId}")
        else:
            print(f"Transaction FAILED")

    async def redirect_cross_shard_request_to_server(self, request_message: bytes, cluster_id: int):
        wrapper = WrapperMessage()
        wrapper.ParseFromString(request_message)
        cross_shard_req = wrapper.crossShardReq
        sender_cluster_id, receiver_cluster_id = cross_shard_req.senderClusterId, cross_shard_req.receiverClusterId

        leader_id = self.leader_per_cluster[cluster_id]
        server_index = LocalConfig.server_id_to_index(leader_id)
        ip, port = LocalConfig.server_ip_port_list[cluster_id][server_index]
        
        print(f"Routingservice redirecting cross-shard transaction request[user {cross_shard_req.senderId} transfers to user {cross_shard_req.receiverId}\
               ${cross_shard_req.amount}] to cluser {cluster_id}, server {leader_id}...")
        
        try:
            response = await utils.send_message_async(ip, port, request_message)
            cross_shard_response = CrossShardRspSerializer.parse(response)

            if cross_shard_response.result == CrossShardResultType.YES:
                id = cross_shard_response.id
                print(f"Transaction request now gets {self.num_reply_for_2PC[id - 1]} YES from leaders...")
                if self.num_reply_for_2PC[id - 1] == 2:
                    # collect all votes, enter 2PC COMMIT phase
                    self.broadcast_commit_message(request_message)

            elif cross_shard_response.result == CrossShardResultType.NO:
                # remove request from the other cluster if there is
                id = cross_shard_response.id
                
                # cluster_to_remove = sender_cluster_id if receiver_cluster_id == cluster_id else receiver_cluster_id
                # self.transaction_request[cluster_to_remove - 1].remove(request_message)
                if self.num_reply_for_2PC[id - 1] != -1:
                    print(f"Transaction request receives NO from leaders...")
                    self.broadcast_abort_message(request_message)
                # update reply status to -1
                self.num_reply_for_2PC[id - 1] = -1
               


        except TimeoutError as e:
            # remove request from the other cluster if there is
            id = cross_shard_response.id
            # cluster_to_remove = sender_cluster_id if receiver_cluster_id == cluster_id else receiver_cluster_id
            # self.transaction_request[cluster_to_remove - 1].remove(request_message)
            if self.num_reply_for_2PC[id - 1] != -1:
                print(f"Transaction request receives reply timeout out from leaders...")
                self.broadcast_abort_message(request_message)
            # update reply status to -1
            self.num_reply_for_2PC[id - 1] = -1


    async def broadcast_commit_message(self, request_message: bytes):
        """2PC Commit/Abort phase: broadcast a COMMIT message to all servers in both clusters."""
        wrapper = WrapperMessage()
        wrapper.ParseFromString(request_message)
        cross_shard_req = wrapper.crossShardReq
        message_commited = CrossShardReqSerializer.to_str(utils.CrossShardPhaseType.COMMIT, cross_shard_req.senderClusterId, cross_shard_req.receiverClusterId,\
                                                 cross_shard_req.senderId, cross_shard_req.receiverId, cross_shard_req.amount, cross_shard_req.id)
        
        sender_cluster_id, receiver_cluster_id = cross_shard_req.senderClusterId, cross_shard_req.receiverClusterId

        print(f"Broadcasting COMMIT to all servers in cluster {sender_cluster_id} and cluster {receiver_cluster_id}...")
        for i in range(LocalConfig.num_server_per_cluster):
            ip, port = LocalConfig.server_ip_port_list[sender_cluster_id][i]
            await utils.send_message_async(ip, port, message_commited, with_response=False)
            ip, port = LocalConfig.server_ip_port_list[receiver_cluster_id][i]
            await utils.send_message_async(ip, port, message_commited, with_response=False)
        print("Transaction completed")


    async def broadcast_abort_message(self, request_message: bytes):
        """2PC Commit/Abort phase: broadcast a ABORT message to all servers in both clusters."""
        wrapper = WrapperMessage()
        wrapper.ParseFromString(request_message)
        cross_shard_req = wrapper.crossShardReq
        message_aborted = CrossShardReqSerializer.to_str(utils.CrossShardPhaseType.ABORT, cross_shard_req.senderClusterId, cross_shard_req.receiverClusterId,\
                                                 cross_shard_req.senderId, cross_shard_req.receiverId, cross_shard_req.amount, cross_shard_req.id)
        sender_cluster_id, receiver_cluster_id = cross_shard_req.senderClusterId, cross_shard_req.receiverClusterId
        print(f"Broadcasting ABORT to all servers in cluster {sender_cluster_id} and cluster {receiver_cluster_id}...")
        for i in range(LocalConfig.num_server_per_cluster):
            ip, port = LocalConfig.server_ip_port_list[sender_cluster_id][i]
            await utils.send_message_async(ip, port, message_aborted, with_response=False)
            ip, port = LocalConfig.server_ip_port_list[receiver_cluster_id][i]
            await utils.send_message_async(ip, port, message_aborted, with_response=False)
