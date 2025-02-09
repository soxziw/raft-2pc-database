import hashlib
from datetime import datetime
from enum import Enum


HANDLE_REQUEST_TIME_DELAY = 3
CLIENT_TIMEOUT = 10
BUFFER_SIZE = 1024
DEFAULT_BALANCE = 10.0
JOB_INTERVAL = 0.1

    

def get_current_time(fmt='%Y-%m-%dT%H:%M:%S'):
    """Get current time in specific string format"""
    return datetime.now().strftime(fmt)