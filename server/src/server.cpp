#include "server.hpp"
#include "ioData.hpp"
#include "executor/printBalanceExecutor.hpp"
#include "executor/printDatastoreExecutor.hpp"

Server::Server(int cluster_id, int server_id,
                    const std::pair<std::string, int>& routing_service_ip_port_pair,
                    const std::vector<std::vector<std::pair<std::string, int>>>& server_ip_port_pairs,
                    int message_timeout_ms) : cluster_id_(cluster_id), server_id_(server_id),
                        routing_service_ip_port_pair_(routing_service_ip_port_pair),
                        server_ip_port_pairs_(server_ip_port_pairs),
                        pretend_fail_(false), keep_running_(true),
                        raft_state_(std::make_shared<RaftState>()), aio_(std::make_shared<AsyncIO>(message_timeout_ms)) {
    std::printf("[Cluster %d][Server %d] Init and start processing.\n", cluster_id, server_id);
    pthread_create(&master_thread_, nullptr, [](void* arg) -> void* {
        Server* server = static_cast<Server*>(arg);
        server->masterThreadFunc();
        return nullptr;
    }, this);

    for (int i = 0; i < num_workers_; ++i) {
        pthread_t worker_thread;
        pthread_create(&worker_thread, nullptr, [](void* arg) -> void* {
            Server* server = static_cast<Server*>(arg);
            server->workerThreadFunc();
            return nullptr;
        }, this);
        worker_threads_.push_back(worker_thread);
    }

    pthread_join(master_thread_, nullptr);
}

void Server::stop() {
    std::printf("[Cluster %d][Server %d] Stop processing.\n", cluster_id_, server_id_);
    keep_running_ = false;

    cond_var_.notify_all();
    // Join worker threads
    for (auto& worker : worker_threads_) {
        pthread_join(worker, nullptr);
    }
    // Close all fds
    if (listen_sockfd_ != -1) {
        close(listen_sockfd_);
    }
}

int Server::process(int client_sock, const WrapperMessage& wrapper_msg) {
    // Process other message types only if not pretending to fail
    switch (wrapper_msg.message_type_case()) {
        case WrapperMessage::kIntraShardReq: {
            // Handle IntraShardReq message
            break;
        }
        case WrapperMessage::kCrossShardReq: {
            // Handle CrossShardReq message
            break;
        }
        case WrapperMessage::kAppendEntriesReq: {
            // Handle AppendEntriesReq message
            break;
        }
        case WrapperMessage::kAppendEntriesRsp: {
            // Handle AppendEntriesRsp message
            break;
        }
        case WrapperMessage::kRequestVoteReq: {
            // Handle RequestVoteReq message
            break;
        }
        case WrapperMessage::kRequestVoteRsp: {
            // Handle RequestVoteRsp message
            break;
        }
        case WrapperMessage::kPrintBalanceReq: {
            // Handle PrintBalanceReq message
            const PrintBalanceReq print_balance_req = wrapper_msg.printbalancereq();
            if (print_balance_req.clusterid() == cluster_id_ && print_balance_req.serverid() == server_id_) {
                PrintBalanceExecutor::executeReq(client_sock, aio_, raft_state_, print_balance_req);
            }
            break;
        }
        case WrapperMessage::kPrintDatastoreReq: {
            // Handle PrintDatastoreReq message
            const PrintDatastoreReq print_datastore_req = wrapper_msg.printdatastorereq();
            if (print_datastore_req.clusterid() == cluster_id_ && print_datastore_req.serverid() == server_id_) {
                PrintDatastoreExecutor::executeReq(client_sock, aio_, raft_state_, print_datastore_req);
            }
            break;
        }
        default: {
            std::cerr << "Unknown message type" << std::endl;
        }
    }
    return 0;
}

void Server::masterThreadFunc() {
    struct sockaddr_in servaddr;
    servaddr.sin_family = AF_INET;
    servaddr.sin_port = htons(server_ip_port_pairs_[cluster_id_][server_id_].second);
    inet_pton(AF_INET, server_ip_port_pairs_[cluster_id_][server_id_].first.c_str(), &(servaddr.sin_addr));

    // Create socket for passive listening
    listen_sockfd_ = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_sockfd_ < 0) {
        std::printf("\033[31m[Error][Cluster %d][Server %d][Server::masterThreadFunc] Failed to create socket.\033[0m\n", cluster_id_, server_id_);
        return;
    }

    if (bind(listen_sockfd_, (struct sockaddr *)&servaddr, sizeof(servaddr)) < 0) {
        close(listen_sockfd_);
        std::printf("\033[31m[Error][Cluster %d][Server %d][Server::masterThreadFunc] Failed to bind to %s:%d.\033[0m\n", 
            cluster_id_, server_id_, server_ip_port_pairs_[cluster_id_][server_id_].first.c_str(), 
            server_ip_port_pairs_[cluster_id_][server_id_].second);
        return;
    }

    if (listen(listen_sockfd_, 3) < 0) {
        close(listen_sockfd_);
        std::printf("\033[31m[Error][Cluster %d][Server %d][Server::masterThreadFunc] Failed to listen on %s:%d.\033[0m\n",
            cluster_id_, server_id_, server_ip_port_pairs_[cluster_id_][server_id_].first.c_str(),
            server_ip_port_pairs_[cluster_id_][server_id_].second);
        return;
    }

    std::printf("[Cluster %d][Server %d] Listening on %s:%d.\n", cluster_id_, server_id_,
        server_ip_port_pairs_[cluster_id_][server_id_].first.c_str(),
        server_ip_port_pairs_[cluster_id_][server_id_].second);

    struct io_uring_params params;
    memset(&params, 0, sizeof(params));
    if (io_uring_queue_init_params(32, &listen_ring_, &params) < 0) {
        throw std::runtime_error("Failed to initialize io_uring");
    }

    IOData* listen_data = new IOData{-1, nullptr, nullptr};
    struct io_uring_sqe *listen_sqe = io_uring_get_sqe(&listen_ring_);
    io_uring_prep_accept(listen_sqe, listen_sockfd_, nullptr, nullptr, 0);
    io_uring_sqe_set_data(listen_sqe, listen_data);
    io_uring_submit(&listen_ring_);

    while (keep_running_) {
        struct io_uring_cqe *listen_cqe;
        int ret = io_uring_wait_cqe(&listen_ring_, &listen_cqe);
        if (ret < 0) continue;

        int client_sock = listen_cqe->res;
        IOData* completed_data = (IOData*)io_uring_cqe_get_data(listen_cqe);
        io_uring_cqe_seen(&listen_ring_, listen_cqe);

        if (completed_data->fd == -1) { // Accept operation
            if (client_sock >= 0) {                
                // Submit read for new connection
                aio_->async_read(client_sock, [this, client_sock](const WrapperMessage& wrapper_msg) {
                    this->handleServer(client_sock, wrapper_msg);
                });
            }
        }
        // Submit new accept
        listen_sqe = io_uring_get_sqe(&listen_ring_);
        io_uring_prep_accept(listen_sqe, listen_sockfd_, nullptr, nullptr, 0);
        io_uring_sqe_set_data(listen_sqe, listen_data);
        io_uring_submit(&listen_ring_);
    }

    delete listen_data;
    // Exit io_uring instance
    io_uring_queue_exit(&listen_ring_);
    // Destruct AsyncIO instance  
    aio_->~AsyncIO();
}

void Server::handleServer(int client_sock, const WrapperMessage& wrapper_msg) {
    std::unique_lock<std::mutex> lock(mutex_);

    if (wrapper_msg.message_type_case() == WrapperMessage::kExit) {
        const Exit exit = wrapper_msg.exit();
        if (exit.clusterid() == cluster_id_ && exit.serverid() == server_id_) {
            stop();
        }
        lock.unlock();
        return;
    }

    // First check if it's a resume message or if we're pretending to fail
    if (wrapper_msg.message_type_case() == WrapperMessage::kResume) {
        const Resume resume = wrapper_msg.resume();
        if (resume.clusterid() == cluster_id_ && resume.serverid() == server_id_) {
            pretend_fail_ = false;
        }
        lock.unlock();
        return;
    }

    if (pretend_fail_) {
        lock.unlock();
        return;
    }

    if (wrapper_msg.message_type_case() == WrapperMessage::kStop) {
        const Stop stop = wrapper_msg.stop();
        if (stop.clusterid() == cluster_id_ && stop.serverid() == server_id_) {
            pretend_fail_ = true;
        }
        lock.unlock();
        return;
    }

    task_queue_.emplace([this, client_sock, wrapper_msg]() {
        this->process(client_sock, wrapper_msg);
    });
    
    lock.unlock();
    cond_var_.notify_one();
}

void Server::workerThreadFunc() {
    while (true) {
        std::unique_lock<std::mutex> lock(mutex_);
        cond_var_.wait(lock, [this]{ return !keep_running_ || !task_queue_.empty(); });
        if (!keep_running_ && task_queue_.empty()) {
            return;
        }
        auto task = std::move(task_queue_.front());
        task_queue_.pop();
        lock.unlock();

        // Process task
        task();
    }
}