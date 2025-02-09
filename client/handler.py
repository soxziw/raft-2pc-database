import socket
import utils
from manager import CrossShardTransactionManager


class TransactionHandler:

    @classmethod
    def transfer(cls, sender_id: int, recipient_id: int, amount: int):
        """Handling a new transfer transaction"""
        sender_cluser_id = cls.get_cluster_id(sender_id)
        recipient_cluser_id = cls.get_cluster_id(recipient_id)
        if sender_cluser_id == recipient_cluser_id:
            cls.send_intra_shard_transaction(sender_cluser_id, sender_id, recipient_id, amount)
        else:
            cls.send_cross_shard_transaction(sender_cluser_id, recipient_cluser_id, sender_id, recipient_id, amount)

    @classmethod
    def send_cross_shard_transaction(cls, sender_cluser_id: int, recipient_cluser_id: int, sender_id: int, recipient_id: int, amount: int):
        """Sending a cross-shard transaction request to a designated server in each of the relevant clusters."""
        CrossShardTransactionManager.send_prepare_message()
    
    @classmethod
    def send_intra_shard_transaction(cls, cluser_id: int, sender_id: int, recipient_id: int, amount: int):
        """Sending a intra-shard transaction request to a designated server within the relevant cluster """
        pass

    @classmethod
    def get_cluster_id(cls, user_id: int) -> int:
        """return the clusterid for the cluster that holds the data item for user"""
        pass

    @classmethod
    def get_balance(cls, user_id: int) -> int:
        """Read the balance of a given user from the database and prints the balance on all server"""
        pass

    @classmethod
    def get_data_store(cls):
        """Return the set of committed transactions on each server."""
        pass


    def get_performance_metrics(cls):
        pass

    def send_message(self, hostname: str, port: int, message):
        """Using the TCP/UDP as the message passing protocal"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(utils.CLIENT_TIMEOUT)
                s.connect((hostname, port))
                s.send(message)
                response = s.recv(utils.BUFFER_SIZE).decode()
                
        except socket.timeout:
            print("socket timeout")
