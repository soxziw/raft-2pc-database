#pragma once
#include <string>

#include "wrapperMessage.pb.h"

void fatal_error(const std::string& syscall);

void serialize_msg_to_buf(WrapperMessage* wrapper_msg, char* buf, int buf_size);

void parse_buf_to_msg(WrapperMessage* wrapper_msg, char* buf, int buf_size);