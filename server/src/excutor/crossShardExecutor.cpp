#include "executor/crossShardExecutor.hpp"
#include "asyncIO.hpp"


void CrossShardExecutor::executeReq(int client_socket, std::shared_ptr<AsyncIO> aio, std::shared_ptr<RaftState> raft_state, const CrossShardReq& req) {

}