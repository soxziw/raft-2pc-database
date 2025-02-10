#include "raftState.hpp"

RaftState::RaftState() : current_term_(0), voted_for_(-1), log_(), local_balance_tb_() {};