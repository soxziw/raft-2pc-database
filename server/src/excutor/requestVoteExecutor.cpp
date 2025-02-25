#include "executor/requestVoteExecutor.hpp"
#include "asyncIO.hpp"


void RequestVoteExecutor::executeReq(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const RequestVoteReq& req) {
    std::printf("[%d:%d][DETAIL] RequestVoteReq: candidateId=%d, term=%d, lastLogIndex=%d, lastLogTerm=%d\n", raft_state->cluster_id_, raft_state->server_id_, req.candidateid(), req.term(), req.lastlogindex(), req.lastlogterm());
    std::printf("[%d:%d][COND] term=%d\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_);
    // Generate response
    WrapperMessage* wrapper_msg = new WrapperMessage;
    RequestVoteRsp* rsp = wrapper_msg->mutable_requestvotersp();
    if ((req.term() < raft_state->current_term_) || (req.term() == raft_state->current_term_ && req.lastlogindex() <= raft_state->lastlogindex())) { // Out-of-date term or not best leader
        rsp->set_term(raft_state->current_term_);
        rsp->set_votegranted(false);
        std::printf("[%d:%d][RequestVoteReq:%d] Out-of-date term or not best leader.\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_);
    } else {
        if (req.term() > raft_state->current_term_) { // Update term
            raft_state->current_term_ = req.term();
            raft_state->voted_for_ = -1;
            std::printf("[%d:%d][RequestVoteReq:%d] Update term.\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_);
        }
        rsp->set_term(raft_state->current_term_);

        if (raft_state->voted_for_ == -1) { // If not vote for anyone, leader need to leave voted_for_ unreset
            rsp->set_votegranted(true);
            raft_state->voted_for_ = req.candidateid();
            raft_state->role_ = Role::FOLLOWER;
            raft_state->heard_heart_beat_ = true;
            std::printf("[%d:%d][RequestVoteReq:%d] Vote for %d.\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_, req.candidateid());
        } else {
            rsp->set_votegranted(false);
        }
    }
    aio->add_write_request_msg(client_socket, wrapper_msg, AIOMessageType::NO_RESPONSE);
    return;
}

void RequestVoteExecutor::executeRsp(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const RequestVoteRsp& rsp) {
    if (raft_state->role_ == Role::CANDIDATE) { // Still remain as candidate
        if (rsp.term() == raft_state->current_term_ && rsp.votegranted()) {
            raft_state->vote_granted_num_++;
            if (raft_state->vote_granted_num_ >= 2) { // Reach majority, become leader
                raft_state->role_ = Role::LEADER;
                raft_state->matched_log_size_ = std::vector<int>(3, raft_state->log_.size());
                std::printf("[%d:%d][RequestVoteRsp:%d] Reach majority, become leader.\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_);
            }
        }
    }
    if (rsp.term() > raft_state->current_term_) { // Update term
        raft_state->current_term_ = rsp.term();
        raft_state->role_ = Role::FOLLOWER;
    }
    close(client_socket);
    return;
}