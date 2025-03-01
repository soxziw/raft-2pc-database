
import time
import aiofiles
import utils
import re, os
from handler import TransactionHandler
from routingservice import RoutingService
import asyncio
from config import LocalConfig
import logging


# Configure logging
logging.basicConfig(
    filename="load_test.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

CONCURRENT_WORKERS = 10


class Client:
    """The client"""
    def __init__(self):
        # self.client_id = client_id
        self.create_time = utils.get_current_time()
        ip, port = LocalConfig.routing_service_ip_port
        self.routing_service = RoutingService(ip,port)
    

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
            elif re.match(r'^(transfer|t)\s+\d+\s+\d+\s+\d+(\.\d+)?$', cmd):
                try:
                    sender, recipient, amount = cmd.split()[1:]
                except ValueError:
                    print('Invalid transfer command')
                    continue
                asyncio.run(self.create_single_transfer(int(sender), int(recipient), int(amount)))
                
            elif re.match(r'^(balance|b)\s+\d+(\.\d+)?$', cmd):
                try:
                    user = cmd.split()[1]
                except ValueError:
                    print('Invalid balance command')
                    continue
                self.print_balance(int(user))
            elif re.match(r'datastore|ds', cmd):
                self.print_data_store()
            elif re.match(r'performance|p', cmd):
                asyncio.run(self.print_performance())
                # import threading
                # thread = threading.Thread(target=lambda: asyncio.run(self.start_load_test()))
                # thread.daemon = True
                # thread.start()
            elif re.match(r'stop|s', cmd):
                try:
                    server_id = cmd.split()[1]
                except ValueError:
                    print('Invalid balance command')
                    continue
                self.stop_server(int(server_id))
            elif re.match(r'resume|r', cmd):
                try:
                    server_id = cmd.split()[1]
                except ValueError:
                    print('Invalid balance command')
                    continue
                self.resume_server(int(server_id))
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


    async def create_single_transfer(self, sender_id: int, recipient_id: int, amount: int):
        """Issue a new transfer transaction"""
        if sender_id is None or recipient_id is None or amount is None:
            print('Invalid transfer command: sender and receiver must not be null')
            return
        if sender_id not in range(1, 3001) or recipient_id not in range(1, 3001):
            print('Invalid transfer command: sender and receiver must be integers from 1 to 3000')
            return
        if amount < 0 or not isinstance(amount, int):
            print("Invalid transfer command: Amount must be positive integer")
            return
        
        print(f"User {sender_id} requests transfering ${amount} to user {recipient_id}...")
        result = await TransactionHandler.transfer(sender_id, recipient_id, amount)
        return result

    def print_balance(self, user_id: int):
        """Print the balance of this user on all servers"""
        if user_id not in range(1, 3001) or user_id not in range(1, 3001):
            print('Invalid balance command: user id must be integers from 1 to 3000')
            return
        print(f"Retrieving balance for user {user_id} from all servers...")
        print('-'*30)
        balance_res =  TransactionHandler.get_balance(user_id)
        for i in range(len(balance_res)):
            print(f"   clusterId: {balance_res[i][0]}, serverId: {balance_res[i][1]}, balance: ${balance_res[i][2]}")
            print('-'*30)

    def print_leader(self):
        """Print the leader of each cluster"""
        print(f"Getting leader information from all clusters...")
        print('-'*30)
        leaders =  self.routing_service.leader_per_cluster
        for i in range(len(leaders)):
            print(f"   clusterId: {i}, leaderId: {leaders[i]}")
            print('-'*30)
        


    def print_data_store(self):
        """Print the committed transactions on all servers"""
        print(f"Retrieving data store from all servers...")
        print('-'*30)
        datastore_res =  TransactionHandler.get_data_store()
        for i in range(len(datastore_res)):
            cluster_id = LocalConfig.get_cluster_id_for_server(i)
            print(f"   clusterId: {cluster_id}, serverId: {i}")
            for entry in datastore_res[i]:
                print(f"   term: {entry[2]}, index: {entry[3]}, command: {entry[4]}")
            print('-'*30)


    async def start_load_test(self, file_path):
        # self.routing_service.latency_for_intra = []
        # with open(os.path.abspath(intra_shard_file_path)) as file:
        #     for line in file:
        #         try:
        #             sender, recipient, amount = line.strip("()\n").split(", ")[0:]
        #         except ValueError:
        #             print('Invalid transfer command')
        #             continue
        #         self.create_single_transfer(int(sender), int(recipient), int(amount))
        # time.sleep(utils.HANDLE_REQUEST_TIME_DELAY)
        # print(f"Calculating latency and throughput for all intra-shard transactions...")
        # print('-'*30)
        # logging.info(f"Calculating latency and throughput for all intra-shard transactions...")
        # logging.info('-'*30)
        # total_latency = 0
        # requests_processed = 0
        # for metric in self.routing_service.latency_for_intra:
        #     if metric.latency_s is not None:
        #         total_latency += metric.latency_s
        #         requests_processed += 1
        # avg_latency = total_latency / requests_processed if requests_processed != 0 else 0
        # avg_throughpput = requests_processed / total_latency if total_latency != 0 else 0
        # print(f"Total requests processed: {requests_processed}/ 1000")
        # print(f"Average latency of intra-shard transactions is : {avg_latency:.3f}s")
        # print(f"Average throughput(Requests Per Second) of intra-shard transactions is : {avg_throughpput:.3f}rps")
        # print('-'*30)
        # logging.info(f"Total requests processed: {requests_processed}/{1000}")
        # logging.info(f"Average latency of intra-shard transactions is : {avg_latency:.3f}s")
        # logging.info(f"Average throughput(Requests Per Second) of intra-shard transactions is : {avg_throughpput:.3f}rps")
        # logging.info('-'*30)

        tasks = []
        async with aiofiles.open(os.path.abspath(file_path), mode='r') as file:
            async for line in file:
                try:
                    sender, recipient, amount = line.strip("()\n").split(", ")[0:]
                    task = self.create_single_transfer(int(sender), int(recipient), int(amount))
                    tasks.append(task)  # Collect async tasks
                except ValueError:
                    print("Invalid transfer command")
                    continue
        start_time = time.time()  # Record global start time
        latencies = await asyncio.gather(*tasks)  # Execute all requests concurrently
        end_time = time.time()  # Record global end time

        total_time = end_time - start_time
        num_requests = len(latencies)
        avg_latency = sum(latencies) / num_requests if num_requests > 0 else 0
        throughput = num_requests / total_time if total_time > 0 else 0

        print(f"Load Testing Completed:")
        print('-'*30)
        print(f"Total Requests: {num_requests}")
        print(f"Total Time: {total_time:.2f} seconds")
        print(f"Throughput: {throughput:.2f} requests per second")
        print(f"Average Latency: {avg_latency:.4f} seconds")
        print('-'*30)

        logging.info(f"Load Testing Completed:")
        logging.info('-'*30)
        logging.info(f"Total Requests: {num_requests}")
        logging.info(f"Total Time: {total_time:.2f} seconds")
        logging.info(f"Throughput: {throughput:.2f} requests per second")
        logging.info(f"Average Latency: {avg_latency:.4f} seconds")
        logging.info('-'*30)


        
    async def print_performance(self):
        """Prints throughput and latency from the time the client initiates a transaction to the time the client process receives a reply message."""                    
        script_dir = os.path.dirname(os.path.abspath(__file__))  # Get current script directory
        intra_shard_file_path = os.path.join(script_dir, 'test/intra_shard_test_500.txt')
        cross_shard_file_path = os.path.join(script_dir, 'test/cross_shard_test_500.txt')
        intra_cross_shard_file_path = os.path.join(script_dir, 'test/intra_cross_shard_test_500.txt')

        print("Start load testing for intra-shard transactions...")
        logging.info("Start load testing for intra-shard transactions...")
        await self.start_load_test(intra_shard_file_path)

        print("Start load testing for cross-shard transactions...")
        logging.info("Start load testing for cross-shard transactions...")

        await self.start_load_test(cross_shard_file_path)

        phase1_latencies = 0
        phase2_latencies = 0
        num_requests = len(self.routing_service.latency_phase1)
        for id, latency in self.routing_service.latency_phase1.items():
            phase1_latencies += latency
        for id, latency in self.routing_service.latency_phase2.items():
            phase2_latencies += latency

        avg_latency_phase1 = phase1_latencies / num_requests if num_requests > 0 else 0
        avg_latency_phase2 = phase2_latencies / num_requests if num_requests > 0 else 0
        print(f"Phase1 Average Latency: {avg_latency_phase1:.4f} seconds")
        print(f"Phase2 Average Latency: {avg_latency_phase2:.4f} seconds")

        print("Start load testing for intra-shard and cross-shard transactions...")
        logging.info("Start load testing for intra-shard and cross-shard transactions...")
        await self.start_load_test(intra_cross_shard_file_path)


    def stop_server(self, server_id):
        if server_id not in range(0, 9):
            print('Invalid stop command: server id must be integers from 0 to 8')
            return
        print(f"Stoping server {server_id}...")
        TransactionHandler.stop(server_id)
    
    def resume_server(self, server_id):
        if server_id not in range(0, 9):
            print('Invalid resume command: server id must be integers from 0 to 8')
            return
        print(f"Resuming server {server_id}...")
        TransactionHandler.resume(server_id)



if __name__ == "__main__":
        
        client = Client()

        # start the routing service
        client.routing_service.start()
        
        # start user interaction
        client.prompt()

        