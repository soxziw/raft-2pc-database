import socket
import select
import asyncio
from datetime import datetime
from config  import LocalConfig


HANDLE_REQUEST_TIME_DELAY = 5
CLIENT_TIMEOUT = 10
BUFFER_SIZE = 1024
DEFAULT_BALANCE = 10.0
JOB_INTERVAL = 0.1
TIMEOUT_ERROR = "TIMEOUT"


class CrossShardPhaseType:
  PREPARE = 0
  COMMIT = 1 
  ABORT = 2


def get_current_time(fmt='%Y-%m-%dT%H:%M:%S'):
    """Get current time in specific string format"""
    return datetime.now().strftime(fmt)

def send_message(hostname: str, port: int, message: bytes, with_response=True, return_timeout=False) -> bytes:
    """Using TCP as the message passing protocol with proper error handling."""
    response = None
    try:
        print(f"sending {message} to {hostname}:{port}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((hostname, port))
            s.setblocking(False)

            # Wait for the socket to be writable
            _, writable, _ = select.select([], [s], [], 1)  # 5s timeout
            if not writable:
                # if return_timeout:
                #     return "TIMEOUT"
                raise TimeoutError("Socket not ready for writing")
            
            s.sendall(message)  # sendall ensures the full message is sent

            if with_response:
                # Wait for the socket to be readable
                readable, _, _ = select.select([s], [], [], 1)
                if not readable:
                    # if return_timeout:
                    #     return "TIMEOUT"
                    raise TimeoutError("Socket not ready for reading")

                response = s.recv(BUFFER_SIZE)
    except socket.timeout:
        if return_timeout:
            return TIMEOUT_ERROR
        raise TimeoutError("Socket operation timed out")
    except BlockingIOError:
        if return_timeout:
            return TIMEOUT_ERROR
        raise RuntimeError("Non-blocking socket operation failed (BlockingIOError)")
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
            response = await asyncio.wait_for(reader.read(BUFFER_SIZE), timeout=3)

        writer.close()
        await writer.wait_closed()

    except asyncio.exceptions.TimeoutError:
        raise TimeoutError("Timeout transaction")
        # print("Socket timeout while receiving response")
    
    return response

async def send_message_to_raft_async(hostname: str, port: int, message: bytes, with_response=True) -> bytes:
    """Using TCP for asynchronous message passing."""
    response = None
    try:
        print(f"sending {message} to {hostname}:{port}...")
        
        reader, writer = await asyncio.open_connection(hostname, port)

        writer.write(message)
        await writer.drain()  # Ensure the message is sent before proceeding

        if with_response:
            try:
                response = await asyncio.wait_for(reader.read(BUFFER_SIZE), timeout=3)
            except asyncio.exceptions.TimeoutError:
                raise TimeoutError("Socket timeout while receiving response")
                # print("Socket timeout while receiving response")

        writer.close()
        await writer.wait_closed()
    except asyncio.exceptions.TimeoutError:
        raise TimeoutError("Socket timeout while connecting")
        # print("Socket timeout while receiving response")
    
    return response