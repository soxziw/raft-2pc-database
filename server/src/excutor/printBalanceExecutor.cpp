#include "executor/printBalanceExecutor.hpp"


void PrintBalanceExecutor::executeReq(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const PrintBalanceReq& msg) {
    WrapperMessage wrapper_msg;
    PrintBalanceRsp* rsp = wrapper_msg.mutable_printbalancersp();
    rsp->set_clusterid(msg.clusterid());
    rsp->set_serverid(msg.serverid());
    rsp->set_dataitemid(msg.dataitemid());

    // Look up balance in local table
    auto it = raft_state->local_balance_tb_.find(msg.dataitemid());
    if (it != raft_state->local_balance_tb_.end()) {
        rsp->set_balance(it->second);
    } else {
        return;
    }

    // Send response back to client
    aio->async_write(client_socket, wrapper_msg, nullptr);
}