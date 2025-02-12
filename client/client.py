
import time
import json
import utils
import re, os, sys
from handler import TransactionHandler



class Client:
    """The client"""
    def __init__(self):
        # self.client_id = client_id
        self.create_time = utils.get_current_time()

    def __repr__(self):
        return f"Client(created_time={self.create_time})"
    

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
                    sender, recipient, amount = cmd.split()[1:]
                except ValueError:
                    print('Invalid transfer command')
                    continue
                self.transfer(int(sender), int(recipient), int(amount))
            elif re.match(r'(balance|bal|b)$', cmd):
                try:
                    user = cmd.split()[1:]
                except ValueError:
                    print('Invalid balance command')
                    continue
                self.print_balance(int(user))
            elif re.match(r'datastore|ds', cmd):
                self.print_data_store()
            elif re.match(r'performance|p', cmd):
                self.print_performance_metrics()
            elif re.match(r'stop|s', cmd):
                try:
                    server_id = cmd.split()[1:]
                except ValueError:
                    print('Invalid balance command')
                    continue
                self.stop(int(server_id))
            elif re.match(r'resume|r', cmd):
                try:
                    server_id = cmd.split()[1:]
                except ValueError:
                    print('Invalid balance command')
                    continue
                self.resume(int(server_id))
            else:
                print('Invalid command, please re-enter')
            print()

    
    def help(self):
        """Help for user interaction"""
        time.sleep(1)
        print('This is the CS271 final project user interface.')
        print('User Commands:')
        print('  1. transfer <sender_id> <recipient_id> <amount_to_transfer> (e.g., transfer 1 2 10, or, t 1 3 5): <sender_id> transfer <amount_to_transfer> to <recipient_id>')
        print('  2. balance <user_id>(or bal, b): print the balance of <user_id>')
        print('  3. datastore (or ds): print the committed transactions of each server')
        print('  4. stop <server_id> (or s): stop the designated server')
        print('  5. resume <server_id> (or r): resume the designated server')
        print('  6. performance (or p): print the throughput and latency of the transaction')
        print('  7. exit (or quit, q): exit the client interface')
        print('Please enter a command:')


    def transfer(self, sender_id: int, recipient_id: int, amount: int):
        """Issue a new transfer transaction"""
        if sender_id is None or recipient_id is None or amount is None:
            print('Invalid transfer command: sender and receiver must not be null')
            return
        if sender_id not in range(1, 3001) or recipient_id not in range(1, 3001):
            print('Invalid transfer command: sender and receiver must be integers from 1 to 3000')
            return
        if amount < 0 or type(amount) is not type(int):
            print("Invalid transfer command: Amount must be positive integer")
            return
        
        print(f"user {sender_id} requests transfering ${amount} to {recipient_id}...")
        TransactionHandler.transfer(sender_id, recipient_id, amount)

    def print_balance(self, user_id: int):
        """Print the balance of this user on all servers"""
        if user_id not in range(1, 3001) or user_id not in range(1, 3001):
            print('Invalid balance command: user id must be integers from 1 to 3000')
            return
        print(f"Retrieving balance for {user_id} from all servers...")
        balance_res =  TransactionHandler.get_balance(user_id)
        for i in range(len(balance_res)):
            print(f"   clusterId:{balance_res[i][0]}, serverId: {balance_res[i][1]}, {balance_res[i][2]}")
        


    def print_data_store(self):
        """Print the committed transactions on all servers"""
        return TransactionHandler.get_data_store()


    def print_performance_metrics(self):
        """Prints throughput and latency from the time the client initiates a transaction to the time the client process receives a reply message."""
        pass

    def stop(self, server_id):
        if server_id not in range(1, 10):
            print('Invalid stop command: server id must be integers from 1 to 9')
            return
        print(f"Stoping server {server_id}...")
        TransactionHandler.stop(server_id)
    
    def resume(self, server_id):
        if server_id not in range(1, 10):
            print('Invalid resume command: server id must be integers from 1 to 9')
            return
        print(f"Resuming server {server_id}...")
        TransactionHandler.resume(server_id)

if __name__ == "__main__":
        client = Client()
        # start user interaction
        client.prompt()