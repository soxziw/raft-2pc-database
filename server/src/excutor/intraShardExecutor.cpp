#include <fmt/format.h>

#include "executor/intraShardExecutor.hpp"
#include "asyncIO.hpp"
#include "intraShardReq.pb.h"
#include "intraShardRsp.pb.h"


void IntraShardExecutor::executeReq(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const IntraShardReq& req) {
    if (raft_state->local_lock_[req.senderid()] || raft_state->local_lock_[req.receiverid()]) {
        WrapperMessage* wrapper_msg = new WrapperMessage;
        IntraShardRsp* rsp = wrapper_msg->mutable_intrashardrsp();
        rsp->set_result(IntraShardResultType::FAIL);
        rsp->set_id(req.id());
        aio->add_write_request_msg(client_socket, wrapper_msg, AIOMessageType::NO_RESPONSE);
        return;
    }
    raft_state->log_.push_back(
        LogEntry {
            raft_state->current_term_,
            static_cast<int>(raft_state->log_.size()),
            fmt::format("{} pays {} ${}",req.senderid(), req.receiverid(), req.amount()),
            req.id(),
            client_socket
        }
    );
    raft_state->local_lock_[req.senderid()] = true;
    raft_state->local_lock_[req.receiverid()] = true;
}