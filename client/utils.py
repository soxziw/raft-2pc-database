import socket
import select
import asyncio
from datetime import datetime
from config  import LocalConfig


HANDLE_REQUEST_TIME_DELAY = 15
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
    """Using TCP as the message passing protocol with proper error handling."""
    response = None
    try:
        print(f"sending {message} to {hostname}:{port}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((hostname, port))
            s.setblocking(False)

            # Wait for the socket to be writable
            _, writable, _ = select.select([], [s], [], 5)  # 5s timeout
            if not writable:
                raise TimeoutError("Socket not ready for writing")
            
            s.sendall(message)  # sendall ensures the full message is sent

            if with_response:
                # Wait for the socket to be readable
                readable, _, _ = select.select([s], [], [], 5)
                if not readable:
                    raise TimeoutError("Socket not ready for reading")

                response = s.recv(BUFFER_SIZE)
    except socket.timeout:
        raise TimeoutError("Socket operation timed out")
    except BlockingIOError:
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
            try:
                response = await asyncio.wait_for(reader.read(BUFFER_SIZE), timeout=LocalConfig.message_timeout_ms)
            except asyncio.TimeoutError:
                raise TimeoutError("Socket timeout while receiving response")

        writer.close()
        await writer.wait_closed()

    except asyncio.TimeoutError:
        raise TimeoutError("Socket timeout while connecting")
    
    return response