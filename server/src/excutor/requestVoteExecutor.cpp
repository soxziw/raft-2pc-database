#include "executor/requestVoteExecutor.hpp"
#include "asyncIO.hpp"


void RequestVoteExecutor::executeReq(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const RequestVoteReq& req) {
    WrapperMessage* wrapper_msg = new WrapperMessage;
    RequestVoteRsp* rsp = wrapper_msg->mutable_requestvotersp();
    if ((req.term() < raft_state->current_term_) || (req.term() == raft_state->current_term_ && req.lastlogindex() < raft_state->lastlogindex())) {
        rsp->set_term(raft_state->current_term_);
        rsp->set_votegranted(false);
    } else {
        if (req.term() > raft_state->current_term_) {
            raft_state->current_term_ = req.term();
            raft_state->voted_for_ = -1;
        }
        rsp->set_term(raft_state->current_term_);

        if (raft_state->voted_for_ == -1) {
            rsp->set_votegranted(true);
            raft_state->voted_for_ = req.candidateid();
        } else {
            rsp->set_votegranted(false);
        }
    }
    aio->add_write_request_msg(client_socket, wrapper_msg, AIOMessageType::NO_RESPONSE);
    return;
}

void RequestVoteExecutor::executeRsp(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const RequestVoteRsp& rsp) {
    if (raft_state->role_ == Role::CANDIDATE) {
        if (rsp.term() == raft_state->current_term_ && rsp.votegranted()) {
            raft_state->vote_granted_num_++;
            if (raft_state->vote_granted_num_ >= 2) {
                raft_state->role_ = Role::LEADER;
                raft_state->next_log_index_ = std::vector<int>(raft_state->log_.size(), 3);
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