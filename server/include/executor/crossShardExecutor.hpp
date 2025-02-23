#pragma once
#include "crossShardReq.pb.h"
#include "crossShardRsp.pb.h"
#include "raftState.hpp"
#include "asyncIO.hpp"

/**
 * CrossShardExecutor - Executor of cross shard messages.
 */
class CrossShardExecutor {
public:
    /**
     * executeReq - Process request.
     *
     * @param client_socket sender of the request
     * @param aio pointer to async I/O layer
     * @param raft_state pointer to raft state object
     * @param req protobuf request
     */
    static void executeReq(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const CrossShardReq& req);
};