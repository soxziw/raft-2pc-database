#pragma once
#include "intraShardReq.pb.h"
#include "intraShardRsp.pb.h"
#include "raftState.hpp"
#include "asyncIO.hpp"


class IntraShardExecutor {
public:
    static void executeReq(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const IntraShardReq& req);
};