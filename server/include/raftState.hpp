#pragma once
#include <string>
#include <vector>
#include <unordered_map>

struct LogEntry {
    int term; // term when entry was received by leader
    int index; // position of entry in the log
    std::string command; // command for state machine
};

class RaftState {
public:
    int current_term_; // Latest term server has seen (initialized to 0 on first boot)
    int voted_for_; // CandidateId that received vote in current term (or null if none)
    std::vector<LogEntry> log_; // log entries
    std::unordered_map<int, int> local_balance_tb_;

    RaftState();
};