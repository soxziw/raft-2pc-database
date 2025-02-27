#include "executor/printDatastoreExecutor.hpp"
#include "asyncIO.hpp"


void PrintDatastoreExecutor::executeReq(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const PrintDatastoreReq& req) { 
    // Generate response
    std::printf("[%d:%d][DETAIL] PrintDatastoreReq: clusterId=%d, serverId=%d\n", raft_state->cluster_id_, raft_state->server_id_, req.clusterid(), req.serverid());
    WrapperMessage* wrapper_msg = new WrapperMessage; 
    PrintDatastoreRsp* rsp = wrapper_msg->mutable_printdatastorersp();
    rsp->set_clusterid(req.clusterid());
    rsp->set_serverid(req.serverid());

    // Copy log entries into response
    for (const auto& entry : raft_state->log_) {
        auto new_entry = rsp->add_entries();
        new_entry->set_term(entry.term);
        new_entry->set_index(entry.index); 
        new_entry->set_command(entry.command);
    }

    // Send response back to client
    std::printf("[%d:%d][DETAIL] PrintDatastoreRsp: clusterId=%d, serverId=%d, logSize=%d\n", raft_state->cluster_id_, raft_state->server_id_, rsp->clusterid(), rsp->serverid(), rsp->entries().size());
    aio->add_write_request_msg(client_socket, wrapper_msg, AIOMessageType::NO_RESPONSE);
}