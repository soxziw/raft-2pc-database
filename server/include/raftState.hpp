#pragma once
#include <string>
#include <vector>
#include <unordered_map>

struct LogEntry {
    int term; // term when entry was received by leader
    int index; // position of entry in the log
    std::string command; // command for state machine
    int id;
    int req_fd;
};

enum Role {
    FOLLOWER = 0,
    CANDIDATE = 1,
    LEADER = 2,
};

class RaftState {
public:
    int cluster_id_;
    int server_id_;
    bool heard_heart_beat_;
    int current_term_; // Latest term server has seen (initialized to 0 on first boot)
    int voted_for_; // CandidateId that received vote in current term (or null if none)
    Role role_;
    int vote_granted_num_;
    std::vector<LogEntry> log_; // log entries
    int log_granted_num_;
    int coming_commit_index_;
    int commit_index_;
    std::vector<int> next_log_index_;
    std::unordered_map<int, int> local_balance_tb_;
    std::unordered_map<int, bool> local_lock_;

    RaftState();
    int lastlogindex();
    int lastlogterm();
    int prevlogindex(int idx);
    int prevlogterm(int idx);
};