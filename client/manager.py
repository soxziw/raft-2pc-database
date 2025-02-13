import socket
import utils



class TransactionManager:



    @classmethod
    def send_message(cls, hostname: str, port: int, message):
        """Using the TCP/UDP as the message passing protocal"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(utils.CLIENT_TIMEOUT)
                s.connect((hostname, port))
                s.send(message)
                response = s.recv(utils.BUFFER_SIZE).decode()
                
        except socket.timeout:
            print("socket timeout")



    @classmethod
    def send_prepare_message(cls):
        """2PC Prepare phase: send PREPARE message to relevant servers"""
        pass

    @classmethod
    def prepare_checker(cls):
        """Set up a timer to check the PREPARE message replies"""
        pass
    
    @classmethod
    def broadcast_commit_message(cls):
        """2PC Commit/Abort phase: broadcast a COMMIT message to all servers in both clusters."""
        pass

    @classmethod
    def broadcast_abort_message(cls):
        """2PC Commit/Abort phase: broadcast a ABORT message to all servers in both clusters."""
        pass