import hashlib
from datetime import datetime
from enum import Enum


HANDLE_REQUEST_TIME_DELAY = 3
CLIENT_TIMEOUT = 10
BUFFER_SIZE = 1024
DEFAULT_BALANCE = 10.0

class TransactionStatus:
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "ABORTED"

class TransactionType:
    INTRA_SHARD = "INTRA_SHARD"
    CROSS_SHARD = "CROSS_SHARD"

class MessageType:
    PREPARE = "PREPARE"
    ABORT = "ABORT"
    ACK = "ACK"
    COMMIT = "COMMIT"
    

def get_current_time(fmt='%Y-%m-%dT%H:%M:%S'):
    """Get current time in specific string format"""
    return datetime.now().strftime(fmt)