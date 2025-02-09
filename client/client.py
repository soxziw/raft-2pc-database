
import time
import json
import utils
import re, os, sys
from handler import TransactionHandler


with open('config.json') as f:
    CONFIG = json.load(f)

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
                self.print_balance(user)
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
        print('This is the CS271 final project user interface.')
        print('User Commands:')
        print('  1. transfer <sender_id> <recipient_id> <amount_to_transfer> (e.g., transfer 1 2 10, or, t 1 3 5): <sender_id> transfer <amount_to_transfer> to <recipient_id>')
        print('  2. balance <user_id>(or bal, b): print the balance of <user_id>')
        print('  3. datastore (or abal, ab): print the committed transactions of each server')
        print('  4. performance (or print, p): print the throughput and latency of the transaction')
        print('  5. exit (or quit, q): exit the client interface')
        print('Please enter a command:')


    def transfer(self, sender_id: int, recipient_id: int, amount: int):
        """Issue a new transfer transaction"""
        if sender_id is None or recipient_id is None or amount is None:
            print('Invalid transfer command: sender and receiver must not be null')
            return
        if sender_id not in range(3000) or recipient_id not in range(3000):
            print('Invalid transfer command: sender and receiver must be from 0 to 2999')
            return
        if amount < 0:
            print("Invalid transfer command: Amount must be positive")
            return
        TransactionHandler.transfer(sender_id, recipient_id, amount)

    def print_balance(self, user_id: int):
        """Print the balance of this client on all servers"""
        return TransactionHandler.get_balance(user_id)


    def print_data_store(self):
        """Print the committed transactions on all servers"""
        return TransactionHandler.get_data_store()


    def print_performance_metrics(self):
        """Prints throughput and latency from the time the client initiates a transaction to the time the client process receives a reply message."""
        pass


if __name__ == "__main__":
        client = Client()
        # start user interaction
        client.prompt()