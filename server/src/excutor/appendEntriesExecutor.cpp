#include "executor/appendEntriesExecutor.hpp"
#include "asyncIO.hpp"


void AppendEntriesExecutor::executeReq(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const AppendEntriesReq& req) {

}

void AppendEntriesExecutor::executeRsp(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const AppendEntriesRsp& rsp) {

}