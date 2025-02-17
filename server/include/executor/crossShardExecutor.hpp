#pragma once
#include "crossShardReq.pb.h"
#include "crossShardRsp.pb.h"
#include "raftState.hpp"
#include "asyncIO.hpp"


class CrossShardExecutor {
public:
    static void executeReq(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const CrossShardReq& req);
};