#pragma once
#include "appendEntriesReq.pb.h"
#include "appendEntriesRsp.pb.h"
#include "raftState.hpp"
#include "asyncIO.hpp"


class AppendEntriesExecutor {
public:
    static void executeReq(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const AppendEntriesReq& req);

    static void executeRsp(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const AppendEntriesRsp& rsp);
};