#include <cstdio>
#include <fmt/format.h>

#include "executor/appendEntriesExecutor.hpp"
#include "intraShardRsp.pb.h"
#include "crossShardRsp.pb.h"
#include "asyncIO.hpp"
#include "aIOServer.hpp"


void AppendEntriesExecutor::executeReq(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const AppendEntriesReq& req) {
    WrapperMessage* wrapper_msg = new WrapperMessage;
    AppendEntriesRsp* rsp = wrapper_msg->mutable_appendentriesrsp();
    rsp->set_serverid(req.serverid());
    if (req.term() < raft_state->current_term_) {
        rsp->set_term(raft_state->current_term_);
        rsp->set_success(false);
    } else {
        if (req.term() > raft_state->current_term_) {
            raft_state->current_term_ = req.term();
        }
        raft_state->role_ = Role::FOLLOWER;
        raft_state->heard_heart_beat_ = true;
        if (raft_state->log_.size() <= req.prevlogindex() || raft_state->log_[req.prevlogindex()].term != req.prevlogterm()) {
            rsp->set_term(raft_state->current_term_);
            rsp->set_success(false);
        } else {
            int log_idx_base = req.prevlogindex() + 1;
            
            int idx = 0;
            for (const Entry& entry : req.entries()) {
                if (!(entry.term() == raft_state->log_[log_idx_base + idx].term) || raft_state->log_.size() <= log_idx_base + idx) {
                    while (raft_state->log_.size() > log_idx_base + idx) {
                        raft_state->log_.pop_back();
                    }
                    break;
                }
                idx++;
            }
            for (auto itr = req.entries().begin() + idx; itr != req.entries().end(); itr++) {
                LogEntry log_entry;
                log_entry.term = itr->term();
                log_entry.index = itr->index(); 
                log_entry.command = itr->command();
                log_entry.id = itr->id();
                log_entry.req_fd = -1;
                raft_state->log_.push_back(log_entry);
            }
            for (int idx = raft_state->commit_index_ + 1; idx <= req.commitindex(); idx++) {
                if (raft_state->log_[idx].command[0] != '[') {
                    int sender_id, receiver_id, amount;
                    std::sscanf(raft_state->log_[idx].command.c_str(), "%d pays %d $%d", &sender_id, &receiver_id, &amount);
                    raft_state->local_balance_tb_[sender_id] -= amount;
                    raft_state->local_balance_tb_[receiver_id] += amount;
                }
            }
            raft_state->commit_index_ = req.commitindex();
            rsp->set_term(raft_state->current_term_);
            rsp->set_success(true);
        }
    }
    aio->add_write_request_msg(client_socket, wrapper_msg, AIOMessageType::NO_RESPONSE);
    return;
}

void AppendEntriesExecutor::executeRsp(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const AppendEntriesRsp& rsp) {
    if (raft_state->role_ == Role::LEADER) {
        if (rsp.term() == raft_state->current_term_) {
            if (rsp.success()) {
                raft_state->log_granted_num_++;
                if (raft_state->log_granted_num_ >= 2) {
                    for (int idx = raft_state->commit_index_ + 1; idx <= raft_state->coming_commit_index_; idx++) {
                        if (raft_state->log_[idx].req_fd != -1) {
                            if (raft_state->log_[idx].command[0] == '[') {
                                if (raft_state->log_[idx].command.substr(0, 9) == "[PREPARE]") {
                                    int sender_id, receiver_id, amount;
                                    std::sscanf(raft_state->log_[idx].command.c_str(), "[PREPARE] %d pays %d $%d", &sender_id, &receiver_id, &amount);
                                    raft_state->local_lock_[sender_id] = false;
                                    raft_state->local_lock_[receiver_id] = false;

                                    WrapperMessage* wrapper_msg = new WrapperMessage;
                                    CrossShardRsp* rsp = wrapper_msg->mutable_crossshardrsp();
                                    rsp->set_result(CrossShardResultType::YES);
                                    rsp->set_id(raft_state->log_[idx].id);
                                    aio->add_write_request_msg(raft_state->log_[idx].req_fd, wrapper_msg, AIOMessageType::NO_RESPONSE);
                                    raft_state->log_[idx].req_fd = -1;
                                }
                            } else {
                                int sender_id, receiver_id, amount;
                                std::sscanf(raft_state->log_[idx].command.c_str(), "%d pays %d $%d", &sender_id, &receiver_id, &amount);
                                raft_state->local_balance_tb_[sender_id] -= amount;
                                raft_state->local_balance_tb_[receiver_id] += amount;
                                raft_state->local_lock_[sender_id] = false;
                                raft_state->local_lock_[receiver_id] = false;

                                WrapperMessage* wrapper_msg = new WrapperMessage;
                                IntraShardRsp* rsp = wrapper_msg->mutable_intrashardrsp();
                                rsp->set_result(IntraShardResultType::SUCCESS);
                                rsp->set_id(raft_state->log_[idx].id);
                                aio->add_write_request_msg(raft_state->log_[idx].req_fd, wrapper_msg, AIOMessageType::NO_RESPONSE);
                                raft_state->log_[idx].req_fd = -1;
                            }
                        }
                    }
                    raft_state->commit_index_ = raft_state->coming_commit_index_;
                }
                raft_state->next_log_index_[rsp.serverid() % SERVER_NUM_PER_CLUSTER] = raft_state->coming_commit_index_ + 1;
            } else {
                raft_state->next_log_index_[rsp.serverid() % SERVER_NUM_PER_CLUSTER]--;
            }
        }
    }
    if (rsp.term() > raft_state->current_term_) {
        raft_state->current_term_ = rsp.term();
        raft_state->role_ = Role::FOLLOWER;
    }
    close(client_socket);
    return;
}