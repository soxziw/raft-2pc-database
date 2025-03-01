#include <fmt/format.h>

#include "executor/intraShardExecutor.hpp"
#include "asyncIO.hpp"
#include "intraShardReq.pb.h"
#include "intraShardRsp.pb.h"


void IntraShardExecutor::executeReq(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const IntraShardReq& req) {
    // Data items in used or sender without enough balance
    std::printf("[%d:%d][DETAIL] IntraShardReq: clusterId=%d, senderId=%d, receiverId=%d, amount=%d, id=%d\n", raft_state->cluster_id_, raft_state->server_id_, req.clusterid(), req.senderid(), req.receiverid(), req.amount(), req.id());
    if (raft_state->local_lock_[req.senderid()] || raft_state->local_lock_[req.receiverid()] || raft_state->local_balance_tb_[req.senderid()] < req.amount()) {
        std::printf("[%d:%d][IntraShardReq:%d] Data items in used or sender without enough balance.\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_);
        // Generate response
        WrapperMessage* wrapper_msg = new WrapperMessage;
        IntraShardRsp* rsp = wrapper_msg->mutable_intrashardrsp();
        rsp->set_result(IntraShardResultType::FAIL);
        rsp->set_id(req.id());
        std::printf("[%d:%d][DETAIL] IntraShardRsp: result=%d, id=%d\n", raft_state->cluster_id_, raft_state->server_id_, rsp->result(), rsp->id());
        aio->add_write_request_msg(client_socket, wrapper_msg, AIOMessageType::NO_RESPONSE);
        return;
    }
    
    // Double check transaction id
    for (const auto& entry : raft_state->log_) {
        if (entry.id == req.id()) {
            std::printf("[%d:%d][IntraShardReq:%d] Transaction id exists.\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_);
            // Generate response
            WrapperMessage* wrapper_msg = new WrapperMessage;
            IntraShardRsp* rsp = wrapper_msg->mutable_intrashardrsp();
            rsp->set_result(IntraShardResultType::FAIL);
            rsp->set_id(req.id());
            std::printf("[%d:%d][DETAIL] IntraShardRsp: result=%d, id=%d\n", raft_state->cluster_id_, raft_state->server_id_, rsp->result(), rsp->id());
            aio->add_write_request_msg(client_socket, wrapper_msg, AIOMessageType::NO_RESPONSE);
            return;
        }
    }

    // Append new log entry
    std::printf("[%d:%d][IntraShardReq:%d] Append new log entry.\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_);
    raft_state->log_.push_back(
        LogEntry {
            raft_state->current_term_,
            static_cast<int>(raft_state->log_.size()),
            fmt::format("{} pays {} ${}",req.senderid(), req.receiverid(), req.amount()),
            req.id(),
            client_socket
        }
    );

    // Lock data items
    raft_state->local_lock_[req.senderid()] = true;
    raft_state->local_lock_[req.receiverid()] = true;
}