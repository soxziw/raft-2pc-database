#include <fmt/format.h>

#include "executor/crossShardExecutor.hpp"
#include "asyncIO.hpp"
#include "util.hpp"
#include "crossShardReq.pb.h"
#include "crossShardRsp.pb.h"


void CrossShardExecutor::executeReq(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const CrossShardReq& req) {
    std::printf("[%d:%d][DETAIL] CrossShardReq: phase=%d, senderClusterId=%d, receiverClusterId=%d, senderId=%d, receiverId=%d, amount=%d, id=%d\n", raft_state->cluster_id_, raft_state->server_id_, req.phase(), req.senderclusterid(), req.receiverclusterid(), req.senderid(), req.receiverid(), req.amount(), req.id());
    if (req.phase() == CrossShardPhaseType::PREPARE) { // Prepare phase
        std::printf("[%d:%d][CrossShardReq:%d] Prepare transaction.\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_);
        // If sender item, of current data shard, is locked or without enough balance; if receiver item, of current data shard, is locked
        if ((req.senderclusterid() == raft_state->cluster_id_ && (raft_state->local_lock_[req.senderid()] || raft_state->local_balance_tb_[req.senderid()] < req.amount()))
            || (req.receiverclusterid() == raft_state->cluster_id_ && raft_state->local_lock_[req.receiverid()])) {
            std::printf("[%d:%d][CrossShardReq:%d] If sender item, of current data shard, is locked or without enough balance; if receiver item, of current data shard, is locked.\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_);
            // Generate response
            WrapperMessage* wrapper_msg = new WrapperMessage;
            CrossShardRsp* rsp = wrapper_msg->mutable_crossshardrsp();
            rsp->set_result(CrossShardResultType::NO);
            rsp->set_id(req.id());
            std::printf("[%d:%d][DETAIL] CrossShardRsp: result=%d, id=%d\n", raft_state->cluster_id_, raft_state->server_id_, rsp->result(), rsp->id());
            aio->add_write_request_msg(client_socket, wrapper_msg, AIOMessageType::NO_RESPONSE);
            return;
        }

        // Double check transaction id and phase
        for (const auto& entry : raft_state->log_) {
            if (entry.id == req.id()) {
                if (entry.command.substr(0, 9) == "[PREPARE]") {
                    std::printf("[%d:%d][CrossShardReq:%d] Transaction id in prepare phase exists.\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_);
                    return;
                }
                if (entry.command.substr(0, 7) == "[ABORT]") {
                    std::printf("[%d:%d][CrossShardReq:%d] Transaction id already aborted.\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_);
                    return;
                }
            }
        }

        // Append prepare log entry
        raft_state->log_.push_back(
            LogEntry {
                raft_state->current_term_,
                static_cast<int>(raft_state->log_.size()),
                fmt::format("[PREPARE] {} pays {} ${}",req.senderid(), req.receiverid(), req.amount()),
                req.id(),
                client_socket
            }
        );

        // Lock data items
        if (req.senderclusterid() == raft_state->cluster_id_) {
            raft_state->local_lock_[req.senderid()] = true;
        }
        if (req.receiverclusterid() == raft_state->cluster_id_) {
            raft_state->local_lock_[req.receiverid()] = true;
        }
    } else if (req.phase() == CrossShardPhaseType::COMMIT) { // Commit phase
        std::printf("[%d:%d][CrossShardReq:%d] Commit transaction.\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_);
        // Double check transaction id and phase
        for (const auto& entry : raft_state->log_) {
            if (entry.id == req.id() && entry.command.substr(0, 8) == "[COMMIT]") {
                std::printf("[%d:%d][CrossShardReq:%d] Transaction id in commit phase exists.\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_);
                return;
            }
        }

        // Append commit log entry
        raft_state->log_.push_back(
            LogEntry {
                raft_state->current_term_,
                static_cast<int>(raft_state->log_.size()),
                fmt::format("[COMMIT] {} pays {} ${}",req.senderid(), req.receiverid(), req.amount()),
                req.id(),
                -1
            }
        );

        // Commit transaction
        if (req.senderclusterid() == raft_state->cluster_id_) {
            raft_state->local_balance_tb_[req.senderid()] -= req.amount();
        }
        if (req.receiverclusterid() == raft_state->cluster_id_) {
            raft_state->local_balance_tb_[req.receiverid()] += req.amount();
        }

        // Update data shard after commit
        update_data_shard(raft_state);
        std::printf("[%d:%d][CrossShardReq:%d] Update data shard after commit.\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_);
        
        // Generate response 
        WrapperMessage* wrapper_msg = new WrapperMessage;
        CrossShardRsp* rsp = wrapper_msg->mutable_crossshardrsp();
        rsp->set_result(CrossShardResultType::ACK);
        rsp->set_id(req.id());
        std::printf("[%d:%d][DETAIL] CrossShardRsp: result=%d, id=%d\n", raft_state->cluster_id_, raft_state->server_id_, rsp->result(), rsp->id());
        aio->add_write_request_msg(client_socket, wrapper_msg, AIOMessageType::NO_RESPONSE);
    } else { // Abort phase
        std::printf("[%d:%d][CrossShardReq:%d] Abort transaction.\n", raft_state->cluster_id_, raft_state->server_id_, raft_state->current_term_);
        // Append abort log entry
        raft_state->log_.push_back(
            LogEntry {
                raft_state->current_term_,
                static_cast<int>(raft_state->log_.size()),
                fmt::format("[ABORT] {} pays {} ${}",req.senderid(), req.receiverid(), req.amount()),
                req.id(),
                -1
            }
        );

        // Generate response
        WrapperMessage* wrapper_msg = new WrapperMessage;
        CrossShardRsp* rsp = wrapper_msg->mutable_crossshardrsp();
        rsp->set_result(CrossShardResultType::ACK);
        rsp->set_id(req.id());
        std::printf("[%d:%d][DETAIL] CrossShardRsp: result=%d, id=%d\n", raft_state->cluster_id_, raft_state->server_id_, rsp->result(), rsp->id());
        aio->add_write_request_msg(client_socket, wrapper_msg, AIOMessageType::NO_RESPONSE);
    }
}