#pragma once
#include <string>
#include <vector>
#include <unistd.h>

#include "asyncIO.hpp"
#include "raftState.hpp"
#include "wrapperMessage.pb.h"

class AIOServer {
public:
    AIOServer(int cluster_id, int server_id,
        const std::pair<std::string, int>& routing_service_ip_port_pair,
        const std::vector<std::vector<std::pair<std::string, int>>>& server_ip_port_pairs,
        int message_timeout_ms);

    int setup_listening_socket(int port);
    
    void broadcast_vote();

    void broadcast_heart_beat();

    void run(int server_socket);

    void process(int client_socket, const WrapperMessage* wrapper_msg);

    int cluster_id_;
    int server_id_;
    std::pair<std::string, int> routing_service_ip_port_pair_;
    std::vector<std::vector<std::pair<std::string, int>>> server_ip_port_pairs_;

    bool pretend_fail_;
    bool keep_running_;
    std::shared_ptr<RaftState> raft_state_;
    std::shared_ptr<AsyncIO> aio_;
};