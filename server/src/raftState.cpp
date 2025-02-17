#include "raftState.hpp"

RaftState::RaftState() : current_term_(0), voted_for_(-1), log_(), local_balance_tb_() {};

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