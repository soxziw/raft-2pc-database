import time
import os, sys, json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

import threading, socket, select
import utils 
from proto.wrapperMessage_pb2 import WrapperMessage
from proto.intraShardRsp_pb2 import IntraShardResultType
from proto.crossShardRsp_pb2 import CrossShardResultType
from serializers.IntraShardRsp import IntraShardRspSerializer
from serializers.CrossShardRsp import CrossShardRspSerializer
from serializers.CrossShardReq import CrossShardReqSerializer
from serializers.IntraShardReq import IntraShardReqSerializer
from config import LocalConfig
import asyncio
import timeloop
from datetime import timedelta


class PerformanceMetricPerRequest:
    def __init__(self, message_size_bytes):
        self.start_time = time.time()
        self.end_time = None
        self.latency_ms = None
        self.latency_s = None
        self.message_size_bits = message_size_bytes * 8
        self.throughput_bps = None

    def calculate_latency_and_throughput(self):
        self.end_time = time.time()
        self.latency_ms = (self.end_time - self.start_time) * 1000  # Convert to ms
        self.latency_s = self.latency_ms / 1000  # Convert ms to seconds
        if self.latency_s > 0:
            self.throughput_bps = self.message_size_bits / self.latency_s  # bits per second
        else:
            self.throughput_bps = float('inf')  # Avoid division by zero



class RoutingService:
    def __init__(self,  hostname: str, port: int):

        self.hostname = hostname
        self.port = port
        self.num_cluster = LocalConfig.num_cluster

        # store the leader of each cluster known via heartbeat
        self.leader_per_cluster = [-1] * self.num_cluster

        self.transaction_id = 0
        # track the number of "YES" in 2PC Commit/Abort phase
        self.num_reply_for_2PC = {}

        # store the request in queue when no leader is elected for that cluster
        self.transaction_request = [[] for _ in range(self.num_cluster)]

        # store the latency of the intra-shard transaction request
        self.conn_for_intra = {}

        # store the latency of the cross-shard transaction request
        self.conn_for_cross = {}
        self.latency_phase1 = {}
        self.latency_phase2 = {}

    def start(self):
        """Start the routing service asynchronously in a new thread."""
        print(f"Starting the routing service on {self.hostname}:{self.port}...")
        asyncio.run(self.server_thread())

    async def server_thread(self):
        """Asynchronous TCP server for handling requests."""
        server = await asyncio.start_server(
            self.handle_connection, self.hostname, self.port
        )
        addr = server.sockets[0].getsockname()
        print(f"Routing service listening on {addr}...")

        async with server:
            await server.serve_forever()

    async def handle_connection(self, reader, writer):
        """Handle incoming connection asynchronously"""
        addr = writer.get_extra_info("peername")
        # print(f"[{time.strftime('%H:%M:%S')}] Accepted connection from {addr}")

        try:
            request_message = await reader.read(utils.BUFFER_SIZE)
            #print(f"[{time.strftime('%H:%M:%S')}] Received request message")
            await self.handle_request(request_message, writer)
            #print(f"[{time.strftime('%H:%M:%S')}] Finished handling request")
        except Exception as e:
            print(f"Error handling connection: {e}")
        # finally:
        #     writer.close()
        #     await writer.wait_closed()

    async def handle_request(self, request_message: bytes, writer):
        """Handle incoming requests asynchronously."""
        wrapper = WrapperMessage()
        wrapper.ParseFromString(request_message)

        if wrapper.HasField("appendEntriesReq"):
            append_entries_req = wrapper.appendEntriesReq
            server_id = append_entries_req.leaderId
            cluster_id = LocalConfig.get_cluster_id_for_server(server_id)
            # no leader for this cluster before
            if self.leader_per_cluster[cluster_id] == -1:
                self.leader_per_cluster[cluster_id] = server_id
                
                print(f"Routing service received AppendEntriesReq from server {server_id}...")
                print(f"Updating leader for cluster {cluster_id} to server {server_id}...")
                
                # Execute pending requests
                pending_requests = self.transaction_request[cluster_id]
                if pending_requests:
                    print(f"Executing pending requests of cluster {cluster_id}...")
                    for request, request_time in pending_requests[:]:  # Create copy to iterate
                        wrapper.ParseFromString(request)
                        if wrapper.HasField("intraShardReq"):
                            intra_shard_req = wrapper.intraShardReq
                            response = await self.redirect_intra_shard_request_to_server(request)
                            conn = self.conn_for_intra[intra_shard_req.id]
                            conn.write(response)
                            await conn.drain()  # Ensure the data is sent before closing the connection
                            conn.close()
                            await conn.wait_closed()

                        elif wrapper.HasField("crossShardReq"):
                            await self.redirect_cross_shard_request_to_server(request, cluster_id)
                    self.transaction_request[cluster_id] = []

            else:
                self.leader_per_cluster[cluster_id] = server_id
            
            writer.close()
            await writer.wait_closed()

        elif wrapper.HasField("requestVoteReq"):
            request_vote_req = wrapper.requestVoteReq
            server_id = request_vote_req.candidateId
            cluster_id = LocalConfig.get_cluster_id_for_server(server_id)
            if self.leader_per_cluster[cluster_id] != -1:
                print(f"Routing service received requestVoteReq from server {server_id}...")
                print(f"Updating leader for cluster {cluster_id} to -1...")
            self.leader_per_cluster[cluster_id] = -1

            writer.close()
            await writer.wait_closed()

        elif wrapper.HasField("intraShardReq"):
            intra_shard_req = wrapper.intraShardReq
            self.transaction_id += 1
            
            print(f"Routing service received intraShardReq from client...")
            message_with_id = IntraShardReqSerializer.to_str(
                clusterId=intra_shard_req.clusterId,
                senderId=intra_shard_req.senderId,
                receiverId=intra_shard_req.receiverId,
                amount=intra_shard_req.amount,
                id=self.transaction_id
            )
            #self.latency_for_intra.append(PerformanceMetricPerRequest(len(request_message)))

            if self.leader_per_cluster[intra_shard_req.clusterId] == -1:
                print(f"\033[33mNo leader for cluster {intra_shard_req.clusterId}, putting request[user {intra_shard_req.senderId} transfers to user {intra_shard_req.receiverId} ${intra_shard_req.amount}] in the queue...\033[0m")
                self.conn_for_intra[self.transaction_id] = writer
                self.transaction_request[intra_shard_req.clusterId].append((message_with_id, time.time()))
                # response = "hello".encode()
                # writer.write(response)
                # await writer.drain()  # Ensure the data is sent before closing the connection
                # writer.close()
                # await writer.wait_closed()
                
            else:
                response = await self.redirect_intra_shard_request_to_server(message_with_id)
                #response = "hello".encode()
                writer.write(response)
                await writer.drain()  # Ensure the data is sent before closing the connection
                writer.close()
                await writer.wait_closed()
                # await self.redirect_intra_shard_request_to_server(message_with_id)

        elif wrapper.HasField("crossShardReq"):
            cross_shard_req = wrapper.crossShardReq
            self.transaction_id += 1
            
            print(f"Routing service received crossShardReq from client...")
            message_with_id = CrossShardReqSerializer.to_str(
                utils.CrossShardPhaseType.PREPARE,
                cross_shard_req.senderClusterId,
                cross_shard_req.receiverClusterId,
                cross_shard_req.senderId,
                cross_shard_req.receiverId,
                cross_shard_req.amount,
                self.transaction_id
            )
            self.latency_phase1[self.transaction_id] = time.time()

            self.num_reply_for_2PC[self.transaction_id] = 0
            #self.latency_for_cross.append(PerformanceMetricPerRequest(len(request_message)))
            self.conn_for_cross[self.transaction_id] = writer
            sender_has_leader = self.leader_per_cluster[cross_shard_req.senderClusterId] != -1
            receiver_has_leader = self.leader_per_cluster[cross_shard_req.receiverClusterId] != -1

            if not sender_has_leader:
                print(f"\033[33mNo leader for sender cluster {cross_shard_req.senderClusterId}, queueing request[user {cross_shard_req.senderId} transfers to user {cross_shard_req.receiverId} ${cross_shard_req.amount}]...\033[0m")
                self.transaction_request[cross_shard_req.senderClusterId].append((message_with_id, time.time()))
            else:
                await self.redirect_cross_shard_request_to_server(message_with_id, cross_shard_req.senderClusterId)

            if not receiver_has_leader:
                print(f"\033[33mNo leader for receiver cluster {cross_shard_req.receiverClusterId}, queueing request[user {cross_shard_req.senderId} transfers to user {cross_shard_req.receiverId} ${cross_shard_req.amount}]...\033[0m")
                self.transaction_request[cross_shard_req.receiverClusterId].append((message_with_id, time.time()))
            else:
                await self.redirect_cross_shard_request_to_server(message_with_id, cross_shard_req.receiverClusterId)
                
            

    async def redirect_intra_shard_request_to_server(self, request_message: bytes):
        wrapper = WrapperMessage()
        wrapper.ParseFromString(request_message)
        intra_shard_req = wrapper.intraShardReq
        leader_id = self.leader_per_cluster[intra_shard_req.clusterId]
        server_index = LocalConfig.server_id_to_index(leader_id)
        ip, port = LocalConfig.server_ip_port_list[intra_shard_req.clusterId][server_index]
        
        print(f"Routingservice redirecting intra-shard transaction request[user {intra_shard_req.senderId} transfers to user {intra_shard_req.receiverId} ${intra_shard_req.amount}] to cluster {intra_shard_req.clusterId}, leader is server {leader_id}[{ip}:{port}]...")
        
        response = None
        response = await utils.send_message_to_raft_async(ip, port, request_message, with_response=True)

        # intra_shard_response = IntraShardRspSerializer.parse(response)
        # if intra_shard_response.result == IntraShardResultType.SUCCESS:
        #     print(f"\033[32mTransaction SUCCEED: user {intra_shard_req.senderId} has transferred ${intra_shard_req.amount} to {intra_shard_req.receiverId}\033[0m")
        # else:
        #     print(f"\033[31mTransaction FAILED: user {intra_shard_req.senderId} fails to transfer ${intra_shard_req.amount} to {intra_shard_req.receiverId}\033[0m")
        
        #self.latency_for_intra[intra_shard_response.id - 1].calculate_latency_and_throughput()
        return response


    async def redirect_cross_shard_request_to_server(self, request_message: bytes, cluster_id: int):
        wrapper = WrapperMessage()
        wrapper.ParseFromString(request_message)
        cross_shard_req = wrapper.crossShardReq
        sender_cluster_id, receiver_cluster_id = cross_shard_req.senderClusterId, cross_shard_req.receiverClusterId

        leader_id = self.leader_per_cluster[cluster_id]
        server_index = LocalConfig.server_id_to_index(leader_id)
        ip, port = LocalConfig.server_ip_port_list[cluster_id][server_index]
        
        print(f"Routingservice redirecting cross-shard transaction request[user {cross_shard_req.senderId} transfers to user {cross_shard_req.receiverId} ${cross_shard_req.amount}] to cluser {cluster_id}, leader is server {leader_id}[{ip}:{port}]...")
        
        cross_shard_response = None
        try:
            response = await utils.send_message_to_raft_async(ip, port, request_message)
            cross_shard_response = CrossShardRspSerializer.parse(response)
        except TimeoutError as e:
            # remove request from the other cluster if there is
            id = cross_shard_req.id
            # cluster_to_remove = sender_cluster_id if receiver_cluster_id == cluster_id else receiver_cluster_id
            # self.transaction_request[cluster_to_remove - 1].remove(request_message)
            if self.num_reply_for_2PC[id] != -1:
                print(f"Transaction request receives reply timeout out from leaders...")
                await self.broadcast_abort_message(request_message)
            # update reply status to -1
            self.num_reply_for_2PC[id] = -1

        if cross_shard_response.result == CrossShardResultType.YES:
            id = cross_shard_response.id
            self.num_reply_for_2PC[id] += 1
            print(f"Transaction request now gets {self.num_reply_for_2PC[id]} YES from leaders...")
            if self.num_reply_for_2PC[id] == 2:
                if id in self.latency_phase1:
                    self.latency_phase1[id] = time.time() - self.latency_phase1[id]
                # collect all votes, enter 2PC COMMIT phase
                await self.broadcast_commit_message(request_message)

        elif cross_shard_response.result == CrossShardResultType.NO:
            # remove request from the other cluster if there is
            id = cross_shard_response.id
            if id in self.latency_phase1:
                    self.latency_phase1[id] = time.time() - self.latency_phase1[id]
            # cluster_to_remove = sender_cluster_id if receiver_cluster_id == cluster_id else receiver_cluster_id
            # self.transaction_request[cluster_to_remove - 1].remove(request_message)
            if self.num_reply_for_2PC[id] != -1:
                print(f"Transaction request receives NO from leaders...")
                await self.broadcast_abort_message(request_message)
            # update reply status to -1
            self.num_reply_for_2PC[id] = -1



    async def broadcast_commit_message(self, request_message: bytes):
        """2PC Commit/Abort phase: broadcast a COMMIT message to all servers in both clusters."""
        wrapper = WrapperMessage()
        wrapper.ParseFromString(request_message)
        cross_shard_req = wrapper.crossShardReq
        message_commited = CrossShardReqSerializer.to_str(utils.CrossShardPhaseType.COMMIT, cross_shard_req.senderClusterId, cross_shard_req.receiverClusterId,\
                                                 cross_shard_req.senderId, cross_shard_req.receiverId, cross_shard_req.amount, cross_shard_req.id)
        
        sender_cluster_id, receiver_cluster_id = cross_shard_req.senderClusterId, cross_shard_req.receiverClusterId

        print(f"Broadcasting COMMIT to all servers in cluster {sender_cluster_id} and cluster {receiver_cluster_id}...")
        self.latency_phase2[cross_shard_req.id] = time.time()
        tasks = []
        for i in range(LocalConfig.num_server_per_cluster):
            ip, port = LocalConfig.server_ip_port_list[sender_cluster_id][i]
            task = utils.send_message_to_raft_async(ip, port, message_commited, with_response=True)
            tasks.append(task)
            ip, port = LocalConfig.server_ip_port_list[receiver_cluster_id][i]
            task = utils.send_message_to_raft_async(ip, port, message_commited, with_response=True)
            tasks.append(task)
        try:
            results = await asyncio.gather(*tasks)
            print(results)
        except Exception as e:
            print(f"Exception caught: {e}")
        self.latency_phase2[cross_shard_req.id] = time.time() - self.latency_phase2[cross_shard_req.id]
        #print("\033[32mTransaction SUCCEED\033[0m")
        #self.latency_for_cross[cross_shard_req.id - 1].calculate_latency_and_throughput()
        writer = self.conn_for_cross[cross_shard_req.id]
        writer.write("Transaction SUCCEED".encode())
        await writer.drain()  # Ensure the data is sent before closing the connection
        writer.close()
        await writer.wait_closed()


    async def broadcast_abort_message(self, request_message: bytes):
        """2PC Commit/Abort phase: broadcast a ABORT message to all servers in both clusters."""
        wrapper = WrapperMessage()
        wrapper.ParseFromString(request_message)
        cross_shard_req = wrapper.crossShardReq
        message_aborted = CrossShardReqSerializer.to_str(utils.CrossShardPhaseType.ABORT, cross_shard_req.senderClusterId, cross_shard_req.receiverClusterId,\
                                                 cross_shard_req.senderId, cross_shard_req.receiverId, cross_shard_req.amount, cross_shard_req.id)
        sender_cluster_id, receiver_cluster_id = cross_shard_req.senderClusterId, cross_shard_req.receiverClusterId
        print(f"Broadcasting ABORT to all servers in cluster {sender_cluster_id} and cluster {receiver_cluster_id}...")
        self.latency_phase2[cross_shard_req.id] = time.time()
        tasks = []
        for i in range(LocalConfig.num_server_per_cluster):
            ip, port = LocalConfig.server_ip_port_list[sender_cluster_id][i]
            task = utils.send_message_to_raft_async(ip, port, message_aborted, with_response=True)
            tasks.append(task)
            ip, port = LocalConfig.server_ip_port_list[receiver_cluster_id][i]
            task = utils.send_message_to_raft_async(ip, port, message_aborted, with_response=True)
            tasks.append(task)
        try:
            results = await asyncio.gather(*tasks)
            print(results)
        except Exception as e:
            print(f"Exception caught: {e}")
        self.latency_phase2[cross_shard_req.id] = time.time() - self.latency_phase2[cross_shard_req.id]
        #self.latency_for_cross[cross_shard_req.id - 1].calculate_latency_and_throughput()
        writer = self.conn_for_cross[cross_shard_req.id]
        writer.write("Transaction ABORTED".encode())
        await writer.drain()  # Ensure the data is sent before closing the connection
        writer.close()
        await writer.wait_closed()


request_queue_checker = timeloop.Timeloop()
    

"""Set up a new task to periodically check the request queue"""
@request_queue_checker.job(interval=timedelta(seconds=utils.JOB_INTERVAL))                          
def process_message_queue():
    wrapper = WrapperMessage()
    for i in range(routing_service.num_cluster):
        pending_requests = routing_service.transaction_request[i]
        new_pending_requests = []
        if not pending_requests:
            continue
        for request, request_time in pending_requests[:]:
            current_time = time.time()
            if current_time - request_time < 3:
                new_pending_requests.append((request, request_time))
                continue
            # remove the request from queue
            wrapper.ParseFromString(request)
            if wrapper.HasField("intraShardReq"):
                intra_shard_req = wrapper.intraShardReq
                print(f"\033[33mNo leader timeout, request[user {intra_shard_req.senderId} transfers to user {intra_shard_req.receiverId} ${intra_shard_req.amount}] removed from queue:\033[0m")

            elif wrapper.HasField("crossShardReq"):
                cross_shard_req = wrapper.crossShardReq
                id = cross_shard_req.id
                print(f"\033[33mNo leader timeout, request[user {cross_shard_req.senderId} transfers to user {cross_shard_req.receiverId} ${cross_shard_req.amount}]  removed from queue:\033[0m")
                if routing_service.num_reply_for_2PC[id] != -1:
                    asyncio.run(routing_service.broadcast_abort_message(request))
                routing_service.num_reply_for_2PC[id] = -1
        routing_service.transaction_request[i] = new_pending_requests


if __name__ == "__main__":
        
        ip, port = LocalConfig.routing_service_ip_port
        routing_service = RoutingService(ip,port)

        request_queue_checker.start()

        # start the routing service
        routing_service.start()
