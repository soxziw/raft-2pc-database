#pragma once
#include <string>
#include <vector>
#include <unistd.h>

#include "asyncIO.hpp"
#include "raftState.hpp"
#include "wrapperMessage.pb.h"

const int SERVER_NUM_PER_CLUSTER = 3;
const int HEAT_BEAT_INTERVAL_MS = 100;
const int TERM_TIMEOUT_MS = 200;
const int MAX_ENTRY_SIZE = 20;
const int DUMP_DATA_INTERVAL_S = 5;

/**
 * AIOServer - Server with async I/O.
 */
class AIOServer {
public:
    /**
     * AIOServer - Initilization.
     *
     * @param cluster_id
     * @param server_id
     * @param routing_service_ip_port_pair ip:port pair of routing service
     * @param server_ip_port_pairs ip:port pairs of server
     * @param message_timeout_ms timeout of message reading and writing
     */
    AIOServer(int cluster_id, int server_id,
        const std::pair<std::string, int>& routing_service_ip_port_pair,
        const std::vector<std::vector<std::pair<std::string, int>>>& server_ip_port_pairs,
        int message_timeout_ms);

    /**
     * setup_listening_socket - Setup listening socket.
     *
     * @param port port to listen to
     */
    int setup_listening_socket(int port);
    
    /**
     * broadcast_vote - Broadcast vote to routing service and other servers in same cluster.
     */
    void broadcast_vote();

    /**
     * broadcast_heart_beat - Broadcast heart beat to routing service and other servers in same cluster.
     */
    void broadcast_heart_beat();

    /**
     * run - Server start running.
     *
     * @param server_socket socket that current server listen to
     */
    void run(int server_socket);

    /**
     * process - Process protobuf message.
     *
     * @param client_socket socket of client
     * @param wrapper_msg protobuf message
     */
    void process(int client_socket, WrapperMessage*& wrapper_msg);

    int cluster_id_;
    int server_id_;
    std::pair<std::string, int> routing_service_ip_port_pair_;
    std::vector<std::vector<std::pair<std::string, int>>> server_ip_port_pairs_;

    bool pretend_fail_; // Pretend to fail, used in stop and resume message
    bool keep_running_; // Used in exit message
    std::shared_ptr<RaftState> raft_state_; // Pointer to raft state object
    std::shared_ptr<AsyncIO> aio_; // Pointer to async I/O layer
};
