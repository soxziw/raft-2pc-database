#include "executor/printDatastoreExecutor.hpp"
#include "asyncIO.hpp"


void PrintDatastoreExecutor::executeReq(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const PrintDatastoreReq& req) { 
    WrapperMessage* wrapper_msg = new WrapperMessage; 
    PrintDatastoreRsp* rsp = wrapper_msg->mutable_printdatastorersp();
    rsp->set_clusterid(req.clusterid());
    rsp->set_serverid(req.serverid());

    // Copy log entries to response
    for (const auto& entry : raft_state->log_) {
        auto new_entry = rsp->add_entries();
        new_entry->set_term(entry.term);
        new_entry->set_index(entry.index); 
        new_entry->set_command(entry.command);
    }

    // Send response back to client
    aio->add_write_request_msg(client_socket, wrapper_msg, AIOMessageType::NO_RESPONSE);
}