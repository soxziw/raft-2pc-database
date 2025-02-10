#include "executor/printDatastoreExecutor.hpp"


void PrintDatastoreExecutor::executeReq(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const PrintDatastoreReq& msg) { 
    WrapperMessage wrapper_msg; 
    PrintDatastoreRsp* rsp = wrapper_msg.mutable_printdatastorersp();
    rsp->set_clusterid(msg.clusterid());
    rsp->set_serverid(msg.serverid());

    // Copy log entries to response
    for (const auto& entry : raft_state->log_) {
        auto new_entry = rsp->add_entries();
        new_entry->set_term(entry.term);
        new_entry->set_index(entry.index); 
        new_entry->set_command(entry.command);
    }

    // Send response back to client
    aio->async_write(client_socket, wrapper_msg, nullptr);
}