#include <fmt/format.h>

#include "executor/crossShardExecutor.hpp"
#include "asyncIO.hpp"
#include "crossShardReq.pb.h"
#include "crossShardRsp.pb.h"


void CrossShardExecutor::executeReq(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const CrossShardReq& req) {
    if (req.phase() == CrossShardPhaseType::PREPARE) {
        if ((req.senderclusterid() == raft_state->cluster_id_ && raft_state->local_lock_[req.senderid()])
            || (req.receiverclusterid() == raft_state->cluster_id_ && raft_state->local_lock_[req.receiverid()])) {
            WrapperMessage* wrapper_msg = new WrapperMessage;
            CrossShardRsp* rsp = wrapper_msg->mutable_crossshardrsp();
            rsp->set_result(CrossShardResultType::NO);
            rsp->set_id(req.id());
            aio->add_write_request_msg(client_socket, wrapper_msg, AIOMessageType::NO_RESPONSE);
            return;
        }
        raft_state->log_.push_back(
            LogEntry {
                raft_state->current_term_,
                static_cast<int>(raft_state->log_.size()),
                fmt::format("[PREPARE] {} pays {} ${}",req.senderid(), req.receiverid(), req.amount()),
                req.id(),
                client_socket
            }
        );
        if (req.senderclusterid() == raft_state->cluster_id_) {
            raft_state->local_lock_[req.senderid()] = true;
        }
        if (req.receiverclusterid() == raft_state->cluster_id_) {
            raft_state->local_lock_[req.receiverid()] = true;
        }
    } else if (req.phase() == CrossShardPhaseType::COMMIT) {
        raft_state->log_.push_back(
            LogEntry {
                raft_state->current_term_,
                static_cast<int>(raft_state->log_.size()),
                fmt::format("[COMMIT] {} pays {} ${}",req.senderid(), req.receiverid(), req.amount()),
                req.id(),
                -1
            }
        );
        if (req.senderclusterid() == raft_state->cluster_id_) {
            raft_state->local_balance_tb_[req.senderid()] -= req.amount();
        }
        if (req.receiverclusterid() == raft_state->cluster_id_) {
            raft_state->local_balance_tb_[req.receiverid()] += req.amount();
        }        
        WrapperMessage* wrapper_msg = new WrapperMessage;
        CrossShardRsp* rsp = wrapper_msg->mutable_crossshardrsp();
        rsp->set_result(CrossShardResultType::ACK);
        rsp->set_id(req.id());
        aio->add_write_request_msg(client_socket, wrapper_msg, AIOMessageType::NO_RESPONSE);
    } else {
        raft_state->log_.push_back(
            LogEntry {
                raft_state->current_term_,
                static_cast<int>(raft_state->log_.size()),
                fmt::format("[ABORT] {} pays {} ${}",req.senderid(), req.receiverid(), req.amount()),
                req.id(),
                -1
            }
        );
        WrapperMessage* wrapper_msg = new WrapperMessage;
        CrossShardRsp* rsp = wrapper_msg->mutable_crossshardrsp();
        rsp->set_result(CrossShardResultType::ACK);
        rsp->set_id(req.id());
        aio->add_write_request_msg(client_socket, wrapper_msg, AIOMessageType::NO_RESPONSE);
    }
}