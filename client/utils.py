import socket
import asyncio
from datetime import datetime
from config  import LocalConfig


HANDLE_REQUEST_TIME_DELAY = 3
CLIENT_TIMEOUT = 10
BUFFER_SIZE = 1024
DEFAULT_BALANCE = 10.0
JOB_INTERVAL = 0.1


class CrossShardPhaseType:
  PREPARE = 0
  COMMIT = 1 
  ABORT = 2


def get_current_time(fmt='%Y-%m-%dT%H:%M:%S'):
    """Get current time in specific string format"""
    return datetime.now().strftime(fmt)

def send_message(hostname: str, port: int, message: bytes, with_response=True) -> bytes:
    """Using the TCP/UDP as the message passing protocal"""
    response = None
    try:
        print(f"sending {message} to {hostname}:{port}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(LocalConfig.message_timeout_ms)
            s.connect((hostname, port))
            s.setblocking(False)
            s.send(message)
            if with_response:
                response = s.recv(BUFFER_SIZE)
    except socket.timeout:
        raise TimeoutError("socket timeout")
    return response
    


async def send_message_async(hostname: str, port: int, message: bytes, with_response=True) -> bytes:
    """Using TCP for asynchronous message passing."""
    response = None
    try:
        print(f"sending {message} to {hostname}:{port}...")
        
        reader, writer = await asyncio.open_connection(hostname, port)

        writer.write(message)
        await writer.drain()  # Ensure the message is sent before proceeding

        if with_response:
            try:
                response = await asyncio.wait_for(reader.read(BUFFER_SIZE), timeout=LocalConfig.message_timeout_ms)
            except asyncio.TimeoutError:
                raise TimeoutError("Socket timeout while receiving response")

        writer.close()
        await writer.wait_closed()

    except asyncio.TimeoutError:
        raise TimeoutError("Socket timeout while connecting")
    
    return response