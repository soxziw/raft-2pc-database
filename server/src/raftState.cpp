#include "raftState.hpp"

RaftState::RaftState(int cluster_id, int server_id) : cluster_id_(cluster_id), server_id_(server_id),
    heard_heart_beat_(false), current_term_(0), voted_for_(-1), role_(Role::FOLLOWER), vote_granted_num_(0), log_(), 
    commit_index_(-1), matched_log_size_(), local_balance_tb_(), local_lock_(), balance_jsonl_{}, modify_items_{} {};

int RaftState::lastlogindex() {
    return log_.empty() ? -1 : log_.back().index;
}

int RaftState::lastlogterm() {
    return log_.empty() ? -1 : log_.back().term;
}

int RaftState::prevlogindex(int idx) {
    return matched_log_size_[idx] - 1;
}

int RaftState::prevlogterm(int idx) {
    return matched_log_size_[idx] == 0 ? -1 : log_[matched_log_size_[idx] - 1].term;
}