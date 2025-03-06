import json
import os



script_dir = os.path.dirname(os.path.abspath(__file__))  # Get current script directory
config_path = os.path.join(script_dir, '../config.json')  # Construct absolute path

with open(os.path.abspath(config_path)) as f:
    CONFIG = json.load(f)



class LocalConfig:
    num_cluster = len(CONFIG['SERVERS']['IP_PORT_PAIRS'])
    users_per_cluster = 1000
    num_server_per_cluster = len(CONFIG['SERVERS']['IP_PORT_PAIRS'][0]) if isinstance(CONFIG['SERVERS'].get('IP_PORT_PAIRS'), list) and CONFIG['SERVERS']['IP_PORT_PAIRS'] else 0
    
    routing_service_ip_port = (CONFIG['ROUTING_SERVICE']['IP_PORT_PAIR']['IP'],int(CONFIG['ROUTING_SERVICE']['IP_PORT_PAIR']['PORT']))
    server_ip_port_list = [[0] * 3 for _ in range(num_cluster)]

    clients_socket_connect_timeout_s = int(CONFIG['CLIENTS']['SOCKET_CONNECT_TIMEOUT_S'])
    clients_sync_message_round_trip_timeout_s = int(CONFIG['CLIENTS']['SYNC_MESSAGE_ROUND_TRIP_TIMEOUT_S']) 
    clients_async_message_round_trip_timeout_s = int(CONFIG['CLIENTS']['ASYNC_MESSAGE_ROUND_TRIP_TIMEOUT_S']) 
    routing_service_message_round_trip_timeout_s = int(CONFIG['ROUTING_SERVICE']['MESSAGE_ROUND_TRIP_TIMEOUT_S']) 
    
    
    for i in range(num_cluster):
        for j in range(num_server_per_cluster):
            server_ip_port_list[i][j] = (CONFIG['SERVERS']['IP_PORT_PAIRS'][i][j]['IP'],int(CONFIG['SERVERS']['IP_PORT_PAIRS'][i][j]['PORT']))
    # print(server_ip_port_list)


    # @property
    # def server_ip_port_list(cls):
    #     return cls.server_ip_port_list
    
    # @property
    # def routing_service_ip_port(cls):
    #     return cls.routing_service_ip_port 
    
    @classmethod
    def get_cluster_id_for_user(cls, user_id: int) -> int:
        """return the clusterid of the cluster that holds the data item for user"""
        return (user_id - 1) // cls.users_per_cluster

    @classmethod
    def get_cluster_id_for_server(cls, server_id: int) -> int:
        """return the clusterid of the cluster that hosts the server"""
        return server_id // cls.num_server_per_cluster
    
    @classmethod
    def server_id_to_index(cls, server_id: int):
        cluster_id = cls.get_cluster_id_for_server(server_id)
        return server_id - cluster_id * cls.num_server_per_cluster
    
    @classmethod
    def server_index_to_id(cls, cluster_id: int, server_index: int):
        return cluster_id * cls.num_server_per_cluster + server_index