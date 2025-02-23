#include "raftState.hpp"

RaftState::RaftState(int cluster_id, int server_id) : cluster_id_(cluster_id), server_id_(server_id),
    heard_heart_beat_(false), current_term_(0), voted_for_(-1), role_(Role::FOLLOWER),
    vote_granted_num_(0), log_(), log_granted_num_(0), coming_commit_index_(-1), commit_index_(-1),
    next_log_index_(), local_balance_tb_(), local_lock_() {};

int RaftState::lastlogindex() {
    return log_.empty() ? -1 : log_.back().index;
}

int RaftState::lastlogterm() {
    return log_.empty() ? -1 : log_.back().term;
}

int RaftState::prevlogindex(int idx) {
    return next_log_index_[idx] - 1;
}

int RaftState::prevlogterm(int idx) {
    return log_.empty() ? -1 : log_[next_log_index_[idx] - 1].term;
}