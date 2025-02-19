#include <string>
#include <vector>
#include <iostream>
#include <unistd.h>
#include <arpa/inet.h>
#include <memory>
#include <liburing.h>
#include <fmt/format.h>

#include "aIOServer.hpp"
#include "util.hpp"
#include "executor/printBalanceExecutor.hpp"
#include "executor/printDatastoreExecutor.hpp"
#include "executor/requestVoteExecutor.hpp"
#include "executor/appendEntriesExecutor.hpp"
#include "executor/intraShardExecutor.hpp"
#include "executor/crossShardExecutor.hpp"


AIOServer::AIOServer(int cluster_id, int server_id,
    const std::pair<std::string, int>& routing_service_ip_port_pair,
    const std::vector<std::vector<std::pair<std::string, int>>>& server_ip_port_pairs,
    int message_timeout_ms) : cluster_id_(cluster_id), server_id_(server_id),
        routing_service_ip_port_pair_(routing_service_ip_port_pair),
        server_ip_port_pairs_(server_ip_port_pairs),
        pretend_fail_(false), keep_running_(true),
        raft_state_(std::make_shared<RaftState>(cluster_id, server_id)),
        aio_(std::make_shared<AsyncIO>(message_timeout_ms)) {
    load_data_shard(raft_state_);
    int server_socket = setup_listening_socket(server_ip_port_pairs[cluster_id][server_id % SERVER_NUM_PER_CLUSTER].second);
    run(server_socket);
}

void AIOServer::broadcast_vote() {
    raft_state_->role_ = Role::CANDIDATE;
    raft_state_->current_term_++;
    raft_state_->voted_for_ = server_id_;
    raft_state_->vote_granted_num_ = 1;

    WrapperMessage* wrapper_msg = new WrapperMessage;
    RequestVoteReq* req = wrapper_msg->mutable_requestvotereq();
    req->set_candidateid(server_id_);
    req->set_term(raft_state_->current_term_);
    req->set_lastlogindex(raft_state_->lastlogindex());
    req->set_lastlogterm(raft_state_->lastlogterm());

    aio_->add_connect_request(routing_service_ip_port_pair_.first, routing_service_ip_port_pair_.second, wrapper_msg, AIOMessageType::WAIT_RESPONSE);

    for (int idx = 0; idx < SERVER_NUM_PER_CLUSTER; idx++) {
        if (idx == server_id_ % SERVER_NUM_PER_CLUSTER) {
            continue;
        }
        WrapperMessage* wrapper_msg = new WrapperMessage;
        RequestVoteReq* req = wrapper_msg->mutable_requestvotereq();
        req->set_candidateid(server_id_);
        req->set_term(raft_state_->current_term_);
        req->set_lastlogindex(raft_state_->lastlogindex());
        req->set_lastlogterm(raft_state_->lastlogterm());

        aio_->add_connect_request(server_ip_port_pairs_[cluster_id_][idx].first, server_ip_port_pairs_[cluster_id_][idx].second, wrapper_msg, AIOMessageType::WAIT_RESPONSE);
    }
}

void AIOServer::broadcast_heart_beat() {
    WrapperMessage* wrapper_msg = new WrapperMessage;
    AppendEntriesReq* req = wrapper_msg->mutable_appendentriesreq();
    req->set_term(raft_state_->current_term_);
    req->set_leaderid(server_id_);

    aio_->add_connect_request(routing_service_ip_port_pair_.first, routing_service_ip_port_pair_.second, wrapper_msg, AIOMessageType::WAIT_RESPONSE);

    raft_state_->coming_commit_index_ = raft_state_->log_.size() - 1;
    for (int idx = 0; idx < SERVER_NUM_PER_CLUSTER; idx++) {
        if (idx == server_id_ % SERVER_NUM_PER_CLUSTER) {
            continue;
        }
        WrapperMessage* wrapper_msg = new WrapperMessage;
        AppendEntriesReq* req = wrapper_msg->mutable_appendentriesreq();
        req->set_term(raft_state_->current_term_);
        req->set_leaderid(server_id_);
        req->set_prevlogindex(raft_state_->prevlogindex(idx));
        req->set_prevlogterm(raft_state_->prevlogterm(idx));
        for (int log_idx = raft_state_->next_log_index_[idx]; log_idx < raft_state_->log_.size(); log_idx++) {
            Entry* entry = req->add_entries();
            entry->set_term(raft_state_->log_[log_idx].term);
            entry->set_index(raft_state_->log_[log_idx].index);
            entry->set_command(raft_state_->log_[log_idx].command);
            entry->set_id(raft_state_->log_[log_idx].id);
        }
        req->set_commitindex(raft_state_->commit_index_);
        req->set_serverid(server_id_ / SERVER_NUM_PER_CLUSTER * SERVER_NUM_PER_CLUSTER + idx);

        aio_->add_connect_request(server_ip_port_pairs_[cluster_id_][idx].first, server_ip_port_pairs_[cluster_id_][idx].second, wrapper_msg, AIOMessageType::WAIT_RESPONSE);
    }
}

int AIOServer::setup_listening_socket(int port) {
    int sock;
    struct sockaddr_in srv_addr;

    sock = socket(PF_INET, SOCK_STREAM, 0);
    if (sock == -1) {
        fatal_error("Failed to create listening socket.");
    }

    int enable = 1;
    if (setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &enable, sizeof(int)) < 0) {
        fatal_error("Failed to set listening socket opt SO_REUSEADDR.");
    }


    memset(&srv_addr, 0, sizeof(srv_addr));
    srv_addr.sin_family = AF_INET;
    srv_addr.sin_port = htons(port);
    srv_addr.sin_addr.s_addr = htonl(INADDR_ANY);

    if (bind(sock, (const struct sockaddr *)&srv_addr, sizeof(srv_addr)) < 0) {
        fatal_error("Failed to bind listening socket.");
    }
                    

    if (listen(sock, 10) < 0) {
        fatal_error(fmt::format("Failed to listen listening socket."));
    }

    std::printf("%s\n", fmt::format("Listening on {}.", port).c_str());

    return (sock);
}

void AIOServer::run(int server_socket) {
    aio_->add_accept_request(server_socket);
    aio_->add_timeout(200);
    while (keep_running_) {
        struct io_uring_cqe* cqe;
        int ret = io_uring_wait_cqe(&(aio_->ring_), &cqe);
        if (ret < 0) {
            continue;
        }

        AIOData* data = (AIOData*)io_uring_cqe_get_data(cqe);
        switch (data->event_type) {
            case AIOEventType::EVENT_TIMEOUT: {
                if (raft_state_->role_ == Role::FOLLOWER) {
                    if (!raft_state_->heard_heart_beat_) {
                        raft_state_->role_ = Role::CANDIDATE;
                        raft_state_->current_term_++;
                        raft_state_->voted_for_ = server_id_;
                        raft_state_->vote_granted_num_ = 1;
                        broadcast_vote();
                    }
                    raft_state_->heard_heart_beat_ = false;
                    aio_->add_timeout(200);
                } else if (raft_state_->role_ == Role::CANDIDATE) {
                    raft_state_->current_term_++;
                    raft_state_->voted_for_ = server_id_;
                    raft_state_->vote_granted_num_ = 1;
                    broadcast_vote();
                    aio_->add_timeout(200);
                } else {
                    broadcast_heart_beat();
                    aio_->add_timeout(50);
                }
                delete data;
                break;
            }
            case AIOEventType::EVENT_ACCEPT: {
                aio_->add_accept_request(server_socket);
                int client_socket = cqe->res;
                aio_->add_read_request(client_socket);
                delete data;
                break;
            }
            case AIOEventType::EVENT_CONNECT: {
                aio_->_add_write_request_buf(data->fd, data->buf, data->buf_size, data->message_type);
                delete data;
                break;
            }
            case AIOEventType::EVENT_READ: {
                WrapperMessage* wrapper_msg;
                parse_buf_to_msg(wrapper_msg, data->buf, cqe->res);
                delete data;
                // process
                process(data->fd, wrapper_msg);
                delete wrapper_msg;
                break;
            }
            case AIOEventType::EVENT_WRITE: {
                if (data->message_type == AIOMessageType::WAIT_RESPONSE) {
                    aio_->add_read_request(data->fd);
                } else {
                    close(data->fd);
                }
                delete data;
                break;
            }
            default: {
                fatal_error(fmt::format("Unknown async I/O event type."));
                delete data;
                break;
            }
        }
        io_uring_cqe_seen(&(aio_->ring_), cqe);
    }
}

void AIOServer::process(int client_socket, const WrapperMessage* wrapper_msg) {
    // Process other message types only if not pretending to fail
    switch (wrapper_msg->message_type_case()) {
        case WrapperMessage::kExit: {
            const Exit exit = wrapper_msg->exit();
            if (exit.clusterid() == cluster_id_ && exit.serverid() == server_id_) {
                keep_running_ = false;
            }
            return;
        }
        case WrapperMessage::kResume: {
            const Resume resume = wrapper_msg->resume();
            if (resume.clusterid() == cluster_id_ && resume.serverid() == server_id_) {
                pretend_fail_ = false;
            }
            return;
        }
        case WrapperMessage::kStop: {
            const Stop stop = wrapper_msg->stop();
            if (stop.clusterid() == cluster_id_ && stop.serverid() == server_id_) {
                pretend_fail_ = true;
            }
            return;
        }
        case WrapperMessage::kIntraShardReq: {
            // Handle IntraShardReq message
            const IntraShardReq intra_shard_req = wrapper_msg->intrashardreq();
            if (intra_shard_req.clusterid() == cluster_id_) {
                IntraShardExecutor::executeReq(client_socket, aio_, raft_state_, intra_shard_req);
            }
            break;
        }
        case WrapperMessage::kCrossShardReq: {
            // Handle CrossShardReq message
            const CrossShardReq cross_shard_req = wrapper_msg->crossshardreq();
            if (cross_shard_req.senderclusterid() == cluster_id_ || cross_shard_req.receiverclusterid() == cluster_id_) {
                CrossShardExecutor::executeReq(client_socket, aio_, raft_state_, cross_shard_req);
            }
            break;
        }
        case WrapperMessage::kAppendEntriesReq: {
            // Handle AppendEntriesReq message
            const AppendEntriesReq append_entries_req = wrapper_msg->appendentriesreq();
            AppendEntriesExecutor::executeReq(client_socket, aio_, raft_state_, append_entries_req);
            break;
        }
        case WrapperMessage::kAppendEntriesRsp: {
            // Handle AppendEntriesRsp message
            const AppendEntriesRsp append_entries_rsp = wrapper_msg->appendentriesrsp();
            AppendEntriesExecutor::executeRsp(client_socket, aio_, raft_state_, append_entries_rsp);
            break;
        }
        case WrapperMessage::kRequestVoteReq: {
            // Handle RequestVoteReq message
            const RequestVoteReq request_vote_req = wrapper_msg->requestvotereq();
            RequestVoteExecutor::executeReq(client_socket, aio_, raft_state_, request_vote_req);
            break;
        }
        case WrapperMessage::kRequestVoteRsp: {
            // Handle RequestVoteRsp message
            const RequestVoteRsp request_vote_rsp = wrapper_msg->requestvotersp();
            RequestVoteExecutor::executeRsp(client_socket, aio_, raft_state_, request_vote_rsp);
            break;
        }
        case WrapperMessage::kPrintBalanceReq: {
            // Handle PrintBalanceReq message
            const PrintBalanceReq print_balance_req = wrapper_msg->printbalancereq();
            if (print_balance_req.clusterid() == cluster_id_ && print_balance_req.serverid() == server_id_) {
                PrintBalanceExecutor::executeReq(client_socket, aio_, raft_state_, print_balance_req);
            }
            break;
        }
        case WrapperMessage::kPrintDatastoreReq: {
            // Handle PrintDatastoreReq message
            const PrintDatastoreReq print_datastore_req = wrapper_msg->printdatastorereq();
            if (print_datastore_req.clusterid() == cluster_id_ && print_datastore_req.serverid() == server_id_) {
                PrintDatastoreExecutor::executeReq(client_socket, aio_, raft_state_, print_datastore_req);
            }
            break;
        }
        default: {
            std::cerr << "Unknown message type" << std::endl;
        }
    }
    return;
}