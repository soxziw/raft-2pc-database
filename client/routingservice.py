import socket
import os, sys, json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
import utils
import threading
from proto.wrapperMessage_pb2 import WrapperMessage
from proto.appendEntriesReq_pb2 import AppendEntriesReq

from serializers.IntraShardReq import IntraShardReqSerializer
from serializers.CrossShardReq import CrossShardReqSerializer
from config import LocalConfig



class RoutingService:
    def __init__(self,  hostname: str, port: int):
        self.hostname = hostname
        self.port = port
        self.num_cluster = LocalConfig.num_cluster
        # Store the leader of each cluster known via heartbeat
        self.leader_per_cluster = [0] * self.num_cluster
        # Track the number of "YES" in 2PC Commit/Abort phase
        self.num_reply = []
        self.intra_shard_request = []
        self.cross_shard_request = []

    def start(self):
        """Start the routing service to listen for heartbeat"""
        threading.Thread(target=self.server_thread, daemon=True).start()

    def server_thread(self):
        """Using the TCP/UDP as the message passing protocal"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind((self.hostname, self.port))
            server.setblocking(False)
            server.listen()
            print(f"Routing service {self.client_id} listening on port {self.port}...")
            while True:
                conn, addr = server.accept()
                # print(f"Accepted connection from {addr}")
                with conn:
                    request_message = conn.recv(utils.BUFFER_SIZE)
                    self.handle_request(conn, request_message)

    def handle_request(self, conn, request_message: bytes):
        """Handling incoming request from other clients"""
        wrapper = WrapperMessage()
        wrapper.ParseFromString(request_message)
        if wrapper.HasField("appendEntriesReq"):
            # TO DO: leader is elected, update leader table
            append_entries_req = wrapper.appendEntriesReq

        elif wrapper.HasField("requestVoteReq"):
            # TO DO: elections are on going, not responding, put the request in request queue
            pass
        elif wrapper.HasField("intraShardReq"):
            """Redirect an intra-shard transaction request to a designated server within the relevant cluster """
            intra_shard_req = wrapper.intraShardReq
        elif wrapper.HasField("crossShardReq"):
            """Redirect a cross-shard transaction request to a designated server in each of the relevant clusters."""
            cross_shard_req = wrapper.cross_shard_req