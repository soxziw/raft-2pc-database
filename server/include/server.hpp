#pragma once
#include <pthread.h>
#include <queue>
#include <unordered_set>
#include <mutex>
#include <condition_variable>
#include <functional>
#include <string>
#include <vector>
#include <iostream>
#include <unistd.h>
#include <arpa/inet.h>
#include <memory>
#include <liburing.h>
#include <pthread.h>

#include "raftState.hpp"
#include "asyncIO.hpp"
#include "wrapperMessage.pb.h"

/**
 * Server - base class of clients.
 */
class Server {
public:
    Server(int cluster_id, int server_id, const std::pair<std::string, int>& routing_service_ip_port_pair, const std::vector<std::vector<std::pair<std::string, int>>>& server_ip_port_pairs, int message_timeout_ms);
    
    /**
     * stop() - stop processing.
     *
     * Signal workers to stop and join threads.
     */
    void stop();

    // /**
    // * sendMsg() - sending message to target server.
    // *
    // * @param target_client_id
    // * @param str
    // */
    // void sendMsg(int target_client_id, std::string& str);

    /**
     * process() - processing.
     *
     * @param str: message received from socket.
     */
    int process(int client_sock, const WrapperMessage& wrapper_msg);

    /**
     * masterThreadFunc() - function that run on master thread.
     */
    void masterThreadFunc();
    
    /**
     * handleServer() - handle message from other server.
     *
     * @param client_sock
     */
    void handleServer(int client_sock, const WrapperMessage& wrapper_msg);

    /**
     * workerThreadFunc() - function that run on worker thread.
     */
    void workerThreadFunc();

    int cluster_id_;
    int server_id_;
    bool pretend_fail_;
    bool keep_running_; /* to terminate master and worker threads */

    std::pair<std::string, int> routing_service_ip_port_pair_;
    std::vector<std::vector<std::pair<std::string, int>>> server_ip_port_pairs_;
    int listen_sockfd_; /* to build up socket connections */
    std::shared_ptr<AsyncIO> aio_; /* io_uring instance */
    struct io_uring listen_ring_;
    int num_workers_ = 5; /* default number of workers */

    /**
     * Producer-consumer model for master and worker threads.
     */
    pthread_t master_thread_; /* producer */
    std::vector<pthread_t> worker_threads_; /* consumer */
    std::queue<std::function<void()>> task_queue_;

    std::mutex mutex_;
    std::condition_variable cond_var_;

    std::shared_ptr<RaftState> raft_state_;
};
