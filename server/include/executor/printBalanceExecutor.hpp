#pragma once
#include "printBalanceReq.pb.h"
#include "printBalanceRsp.pb.h"
#include "raftState.hpp"
#include "asyncIO.hpp"


class PrintBalanceExecutor {
public:
    static void executeReq(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const PrintBalanceReq& msg);
};