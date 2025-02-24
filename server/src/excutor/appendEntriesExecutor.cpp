#include <cstdio>
#include <fmt/format.h>

#include "executor/appendEntriesExecutor.hpp"
#include "intraShardRsp.pb.h"
#include "crossShardRsp.pb.h"
#include "asyncIO.hpp"
#include "aIOServer.hpp"
#include "util.hpp"


void AppendEntriesExecutor::executeReq(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const AppendEntriesReq& req) {
    // Generate response
    WrapperMessage* wrapper_msg = new WrapperMessage;
    AppendEntriesRsp* rsp = wrapper_msg->mutable_appendentriesrsp();
    rsp->set_serverid(req.serverid());
    if (req.term() < raft_state->current_term_) { // Out-of-date term
        rsp->set_term(raft_state->current_term_);
        rsp->set_success(false);
        std::printf("[%d:%d][AppendEntriesReq:%d] Out-of-date term or not best leader.\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_);
    } else { // Downlevel to follower and replicate log
        if (req.term() > raft_state->current_term_) { // Update term
            raft_state->current_term_ = req.term();
            std::printf("[%d:%d][AppendEntriesReq:%d] Update term.\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_);
        }
        raft_state->role_ = Role::FOLLOWER;
        raft_state->heard_heart_beat_ = true;
        if ((int)raft_state->log_.size() <= req.prevlogindex() || (req.prevlogindex() >= 0 && raft_state->log_[req.prevlogindex()].term != req.prevlogterm())) { // Log entry not exist or not match in current server
            rsp->set_term(raft_state->current_term_);
            rsp->set_success(false);
            std::printf("[%d:%d][AppendEntriesReq:%d] Log entry not exist or not match in current server.\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_);
        } else {
            int log_idx_base = req.prevlogindex() + 1;
            
            // Find the first unmatched log entry
            int idx = 0;
            for (const Entry& entry : req.entries()) {
                // Unmatch or end of log of current server
                if (!(entry.term() == raft_state->log_[log_idx_base + idx].term) || (int)raft_state->log_.size() <= log_idx_base + idx) {
                    while ((int)raft_state->log_.size() > log_idx_base + idx) {
                        raft_state->log_.pop_back();
                    }
                    break;
                }
                idx++;
            }
            
            // Copy unmatched log entries to current server
            for (auto itr = req.entries().begin() + idx; itr != req.entries().end(); itr++) {
                LogEntry log_entry;
                log_entry.term = itr->term();
                log_entry.index = itr->index(); 
                log_entry.command = itr->command();
                log_entry.id = itr->id();
                log_entry.req_fd = -1;
                raft_state->log_.push_back(log_entry);
            }

            // Commit log entries
            for (int idx = raft_state->commit_index_ + 1; idx <= req.commitindex(); idx++) {
                if (raft_state->log_[idx].command[0] != '[') { // Only commit intra-shard transaction
                    int sender_id, receiver_id, amount;
                    std::sscanf(raft_state->log_[idx].command.c_str(), "%d pays %d $%d", &sender_id, &receiver_id, &amount);
                    raft_state->local_balance_tb_[sender_id] -= amount;
                    raft_state->local_balance_tb_[receiver_id] += amount;
                }
                std::printf("[%d:%d][AppendEntriesReq:%d] Commit: %s.\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_, raft_state->log_[idx].command.c_str());
            }
            if (raft_state->commit_index_ != req.commitindex()) {
                raft_state->commit_index_ = req.commitindex();
            }
            rsp->set_term(raft_state->current_term_);
            rsp->set_success(true);
            std::printf("[%d:%d][AppendEntriesReq:%d] Success.\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_);
        }
    }
    aio->add_write_request_msg(client_socket, wrapper_msg, AIOMessageType::NO_RESPONSE);
    return;
}

void AppendEntriesExecutor::executeRsp(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const AppendEntriesRsp& rsp) {
    if (raft_state->role_ == Role::LEADER) { // Still remain leader
        if (rsp.term() == raft_state->current_term_) { // Remain in same term
            if (rsp.success()) { // Success
                raft_state->log_granted_num_++;
                if (raft_state->log_granted_num_ >= 2 && raft_state->coming_commit_index_ >= 0 && raft_state->log_[raft_state->coming_commit_index_].term == raft_state->current_term_) { // Reach majority and last log in current term
                    std::printf("[%d:%d][AppendEntriesRsp:%d] Reach majority and last log in current term.\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_);
                    for (int idx = raft_state->commit_index_ + 1; idx <= raft_state->coming_commit_index_; idx++) {
                        if (raft_state->log_[idx].command[0] == '[') { // Cross-shard transactions
                            if (raft_state->log_[idx].command.substr(0, 9) == "[PREPARE]") {
                                // Unlock data items
                                int sender_id, receiver_id, amount;
                                std::sscanf(raft_state->log_[idx].command.c_str(), "[PREPARE] %d pays %d $%d", &sender_id, &receiver_id, &amount);
                                raft_state->local_lock_[sender_id] = false;
                                raft_state->local_lock_[receiver_id] = false;

                                if (raft_state->log_[idx].req_fd != -1) { // Need response
                                    // Generate response
                                    WrapperMessage* wrapper_msg = new WrapperMessage;
                                    CrossShardRsp* rsp = wrapper_msg->mutable_crossshardrsp();
                                    rsp->set_result(CrossShardResultType::YES);
                                    rsp->set_id(raft_state->log_[idx].id);
                                    aio->add_write_request_msg(raft_state->log_[idx].req_fd, wrapper_msg, AIOMessageType::NO_RESPONSE);
                                    raft_state->log_[idx].req_fd = -1;
                                }
                            }
                        } else { // Intra-shard transactions
                            // Commit log entries
                            int sender_id, receiver_id, amount;
                            std::sscanf(raft_state->log_[idx].command.c_str(), "%d pays %d $%d", &sender_id, &receiver_id, &amount);
                            raft_state->local_balance_tb_[sender_id] -= amount;
                            raft_state->local_balance_tb_[receiver_id] += amount;
                            raft_state->local_lock_[sender_id] = false;
                            raft_state->local_lock_[receiver_id] = false;

                            if (raft_state->log_[idx].req_fd != -1) { // Need response
                                WrapperMessage* wrapper_msg = new WrapperMessage;
                                IntraShardRsp* rsp = wrapper_msg->mutable_intrashardrsp();
                                rsp->set_result(IntraShardResultType::SUCCESS);
                                rsp->set_id(raft_state->log_[idx].id);
                                aio->add_write_request_msg(raft_state->log_[idx].req_fd, wrapper_msg, AIOMessageType::NO_RESPONSE);
                                raft_state->log_[idx].req_fd = -1;
                            }
                        }
                        std::printf("[%d:%d][AppendEntriesRsp:%d] Commit: %s.\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_, raft_state->log_[idx].command.c_str());
                    }
                    if (raft_state->commit_index_ != raft_state->coming_commit_index_) {
                        // Update data shard after commit
                        update_data_shard(raft_state);
                        std::printf("[%d:%d][AppendEntriesRsp:%d] Update data shard after commit.\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_);
                        raft_state->commit_index_ = raft_state->coming_commit_index_;
                    }
                }
                raft_state->matched_log_size_[rsp.serverid() % SERVER_NUM_PER_CLUSTER] = raft_state->coming_commit_index_ + 1;
            } else { // Fail, decrease matched log size
                std::printf("[%d:%d][AppendEntriesRsp:%d] Fail, decrease matched log size.\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_);
                raft_state->matched_log_size_[rsp.serverid() % SERVER_NUM_PER_CLUSTER]--;
            }
        }
    }
    if (rsp.term() > raft_state->current_term_) { // Update term
        std::printf("[%d:%d][AppendEntriesRsp:%d] Update term.\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_);
        raft_state->current_term_ = rsp.term();
        raft_state->role_ = Role::FOLLOWER;
    }
    close(client_socket);
    return;
}