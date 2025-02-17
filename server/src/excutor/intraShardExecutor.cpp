#include "executor/intraShardExecutor.hpp"
#include "asyncIO.hpp"


void IntraShardExecutor::executeReq(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const IntraShardReq& req) {
    
}