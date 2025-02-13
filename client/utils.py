import socket, json
from datetime import datetime
from enum import Enum

import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))


HANDLE_REQUEST_TIME_DELAY = 3
CLIENT_TIMEOUT = 10
BUFFER_SIZE = 1024
DEFAULT_BALANCE = 10.0
JOB_INTERVAL = 0.1


with open('../config.json') as f:
    CONFIG = json.load(f)
    

def get_current_time(fmt='%Y-%m-%dT%H:%M:%S'):
    """Get current time in specific string format"""
    return datetime.now().strftime(fmt)

def send_message(hostname: str, port: int, message: bytes, with_response=True) -> bytes:
    """Using the TCP/UDP as the message passing protocal"""
    response = None
    try:
        print(f"sending {message} to {hostname}:{port}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(CONFIG['MESSAGE_TIMEOUT_MS'])
            s.connect((hostname, port))
            s.send(message)
            if with_response:
                response = s.recv(BUFFER_SIZE)
    except socket.timeout:
        raise TimeoutError("socket timeout")
    return response