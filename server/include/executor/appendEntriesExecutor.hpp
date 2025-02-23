#pragma once
#include "appendEntriesReq.pb.h"
#include "appendEntriesRsp.pb.h"
#include "raftState.hpp"
#include "asyncIO.hpp"

/**
 * AppendEntriesExecutor - Executor of append entries messages.
 */
class AppendEntriesExecutor {
public:
    /**
     * executeReq - Process request.
     *
     * @param client_socket sender of the request
     * @param aio pointer to async I/O layer
     * @param raft_state pointer to raft state object
     * @param req protobuf request
     */
    static void executeReq(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const AppendEntriesReq& req);

    /**
     * executeRsp - Process response.
     *
     * @param client_socket sender of the response
     * @param aio pointer to async I/O layer
     * @param raft_state pointer to raft state object
     * @param rsp protobuf response
     */
    static void executeRsp(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const AppendEntriesRsp& rsp);
};