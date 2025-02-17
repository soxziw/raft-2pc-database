#include <cerrno>
#include <cstdlib>
#include <memory>

#include "util.hpp"

void fatal_error(const std::string& syscall) {
    perror(syscall.c_str());
    exit(1);
}

void serialize_msg_to_buf(WrapperMessage* wrapper_msg, char* buf, int buf_size) {
    std::string serialized;
    wrapper_msg->SerializeToString(&serialized);
    delete wrapper_msg;
    
    buf = new char[serialized.size()];
    memcpy(buf, serialized.data(), serialized.size());
    buf_size = serialized.size();
}

void parse_buf_to_msg(WrapperMessage* wrapper_msg, char* buf, int buf_size) {
    wrapper_msg->ParseFromArray(buf, buf_size);
    delete[] buf;
}