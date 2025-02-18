#include "executor/printBalanceExecutor.hpp"
#include "asyncIO.hpp"


void PrintBalanceExecutor::executeReq(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const PrintBalanceReq& req) {
    WrapperMessage* wrapper_msg = new WrapperMessage;
    PrintBalanceRsp* rsp = wrapper_msg->mutable_printbalancersp();
    rsp->set_clusterid(req.clusterid());
    rsp->set_serverid(req.serverid());
    rsp->set_dataitemid(req.dataitemid());

    // Look up balance in local table
    auto it = raft_state->local_balance_tb_.find(req.dataitemid());
    if (it != raft_state->local_balance_tb_.end()) {
        rsp->set_balance(it->second);
    } else {
        return;
    }

    // Send response back to client
    aio->add_write_request_msg(client_socket, wrapper_msg, AIOMessageType::NO_RESPONSE);
}