import threading
import timeloop
import socket
import time
import json
from datetime import timedelta
from typing import List
import utils
import re, os, sys
from utils import TransactionStatus, MessageType, TransactionType


with open('config.json') as f:
    CONFIG = json.load(f)

class Client:
    """The client"""
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.create_time = utils.get_current_time()

    def __repr__(self):
        return f"Client(id={self.client_id}, created_time={self.create_time})"
    

    def prompt(self):
        self.help()
        """User interacting interface for intra-shard and cross-shard transaction"""
        while True:
            cmd = input('>>> ').strip().lower()
            if re.match(r'(exit|quit|q)$', cmd):
                print('Exiting...')
                os._exit(0)
            elif re.match(r'^(transfer|t)\s+\d+\s+\d+(\.\d+)?$', cmd):
                try:
                    recipient, amount = cmd.split()[1:]
                except ValueError:
                    print('Invalid transfer command')
                    continue
                self.send_transaction(int(recipient), float(amount))
            elif re.match(r'(balance|bal|b)$', cmd):
                self.print_balance()
            elif re.match(r'datastore|ds', cmd):
                self.print_data_store()
            elif re.match(r'|p', cmd):
                self.print_performance_metrics()
            else:
                print('Invalid command, please re-enter')
            print()

    
    def help(self):
        """Help for user interaction"""
        time.sleep(1)
        print('This is the CS271 blockchain client interface.')
        print('User Commands:')
        print('  1. transfer <recipient_id> <amount_to_transfer> (e.g., transfer 2 10, or, t 3 5): transfer <amount_to_transfer> to <recipient_id>')
        print('  2. balance (or bal, b): print the balance of the client')
        print('  3. datastore (or abal, ab): print the committed transactions of each server')
        print('  4. performance (or print, p): print the throughput and latency of the transaction')
        print('  5. exit (or quit, q): exit the client interface')
        print('Please enter a command:')


    def send_transaction(self, message: str):
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


    def transfer(self):
        pass

    def print_balance(self):
        pass


    def print_data_store(self):
        pass


    def print_performance_metrics(self):
        pass


if __name__ == "__main__":
        client = Client(client_id='A')
        # start user interaction
        client.prompt()