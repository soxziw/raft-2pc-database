#pragma once
#include "requestVoteReq.pb.h"
#include "requestVoteRsp.pb.h"
#include "raftState.hpp"
#include "asyncIO.hpp"

/**
 * RequestVoteExecutor - Executor of request vote messages.
 */
class RequestVoteExecutor {
public:
    /**
     * executeReq - Process request.
     *
     * @param client_socket sender of the request
     * @param aio pointer to async I/O layer
     * @param raft_state pointer to raft state object
     * @param req protobuf request
     */
    static void executeReq(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const RequestVoteReq& req);

    /**
     * executeRsp - Process response.
     *
     * @param client_socket sender of the response
     * @param aio pointer to async I/O layer
     * @param raft_state pointer to raft state object
     * @param rsp protobuf response
     */
    static void executeRsp(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const RequestVoteRsp& rsp);
};