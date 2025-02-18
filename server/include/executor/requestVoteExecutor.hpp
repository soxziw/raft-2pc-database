#pragma once
#include "requestVoteReq.pb.h"
#include "requestVoteRsp.pb.h"
#include "raftState.hpp"
#include "asyncIO.hpp"


class RequestVoteExecutor {
public:
    static void executeReq(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const RequestVoteReq& req);

    static void executeRsp(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const RequestVoteRsp& rsp);
};