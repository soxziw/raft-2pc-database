#pragma once
#include "printDatastoreReq.pb.h"
#include "printDatastoreRsp.pb.h"
#include "raftState.hpp"
#include "asyncIO.hpp"


class PrintDatastoreExecutor {
public:
    static void executeReq(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const PrintDatastoreReq& req);
};