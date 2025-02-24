#pragma once
#include <string>

#include "raftState.hpp"
#include "wrapperMessage.pb.h"

/**
 * fatal_error - Print fatal error and terminate process.
 *
 * @param str 
 */
void fatal_error(const std::string& str);

/**
 * load_data_shard - Load data shard into local balance tabel.
 * Each data shard stored in a jsonl file.
 *
 * @param raft_state raft state to udpate.
 */
void load_data_shard(std::shared_ptr<RaftState> raft_state);

/**
 * update_data_shard - Update data shard into local balance tabel.
 * Each data shard stored in a jsonl file.
 *
 * @param raft_state raft state to dump.
 */
void update_data_shard(std::shared_ptr<RaftState> raft_state);

/**
 * serialize_msg_to_buf - Serialize protobuf message into char array buffer.
 *
 * @param wrapper_msg pointer of protobuf message to serialize.
 * @param buf pointer of char array buffer to fill.
 * @param buf_size size of content filled in the buffer.
 */
void serialize_msg_to_buf(WrapperMessage*& wrapper_msg, char*& buf, int& buf_size);

/**
 * parse_buf_to_msg - Parse char array buffer into protobuf message.
 *
 * @param wrapper_msg pointer of protobuf message to parse.
 * @param buf pointer of char array buffer to extract.
 * @param buf_size size of content in the buffer.
 */
void parse_buf_to_msg(WrapperMessage*& wrapper_msg, char*& buf, int& buf_size);