#pragma once
#include <string>
#include <vector>
#include <unordered_map>

/**
 * LogEntry - Entry that store each log item.
 */
struct LogEntry {
    int term; // Term when entry was received by leader
    int index; // Position of entry in the log
    std::string command; // Command for state machine
    int id; // Unique id of the log item
    int req_fd; // Fd of request socket, -1 as default, != -1 is waiting for response
};

/**
 * Role - Role of the server.
 */
enum Role {
    FOLLOWER = 0, // Follower, follow commands
    CANDIDATE = 1, // Candidate, wait for vote
    LEADER = 2, // Leader, process transaction
};

/**
 * RaftState - Varients for raft protocol.
 */
class RaftState {
public:
    int cluster_id_; // Cluster id of current server
    int server_id_; // Id of current server
    bool heard_heart_beat_; // Have heard heart beat from leader or not in last period 
    int current_term_; // Latest term server has seen (initialized to 0 on first boot)
    int voted_for_; // CandidateId that received vote in current term (or null if none)
    Role role_; // Role of current server
    int vote_granted_num_; // Number of vote received in this term
    std::vector<LogEntry> log_; // Log entries
    int log_granted_num_; // Number of success log replication in this term
    int coming_commit_index_; // Coming commit index in this term, if log_granted_num_ >= majority
    int commit_index_; // Commited index
    std::vector<int> matched_log_size_; // Matched log size for each server
    std::unordered_map<int, int> local_balance_tb_; // Local balance table
    std::unordered_map<int, bool> local_lock_; // Local lock for data items

    /**
     * RaftState - Initialization.
     *
     * @param cluster_id
     * @param server_id
     */
    RaftState(int cluster_id, int server_id);
    
    /**
     * lastlogindex - last log index of current server.
     *
     * Used in election rule.
     */
    int lastlogindex();

    /**
     * lastlogterm - term of last log index of current server.
     *
     * Used in election rule.
     */
    int lastlogterm();

    /**
     * prevlogindex - previous replicated log index of a target server.
     *
     * @param idx index of target server in current cluster.
     */
    int prevlogindex(int idx);

    /**
     * prevlogterm - term of previous replicated log index of a target server.
     *
     * @param idx index of target server in current cluster.
     */
    int prevlogterm(int idx);
};