#include <cstdio>
#include "executor/appendEntriesExecutor.hpp"
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
                raft_state->log_.push_back(log_entry);
            }
            for (int idx = raft_state->commit_index_ + 1; idx <= req.commitindex(); idx++) {
                std::string cmd = raft_state->log_[idx].command;
                if (cmd[0] == '[') {
                    if (cmd.substr(0, 8) != "[COMMIT]") {
                        continue;
                    } else {
                        cmd = cmd.substr(9, cmd.size() - 9);
                    }
                }
                int sender_id, receiver_id, amount;
                std::sscanf(cmd.c_str(), "%d pays %d $%d", &sender_id, &receiver_id, &amount);
                raft_state->local_balance_tb_[sender_id] -= amount;
                raft_state->local_balance_tb_[receiver_id] += amount;
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