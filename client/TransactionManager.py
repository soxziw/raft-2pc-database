
import socket


def send_message(self, message: str):
    """Using the TCP/UDP as the message passing protocal"""
    hostname = CONFIG['SERVER']["S1"]["HOST_IP"]
    port = CONFIG['SERVER']["S1"]["HOST_PORT"]
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(utils.CLIENT_TIMEOUT)
            s.connect((hostname, port))
            s.send(json.dumps(message).encode())
            response = json.loads(s.recv(utils.BUFFER_SIZE).decode())
            
    except socket.timeout:
        print("socket timeout")




def send_prepare_message(self):
    pass

def broadcast_commit_message(self):
    pass

def broadcast_abort_message(self):
    pass