#pragma once
#include <liburing.h>
#include <memory>

#include "wrapperMessage.pb.h"

enum AIOEventType {
    EVENT_ACCEPT = 1,
    EVENT_CONNECT = 2,
    EVENT_READ = 3,
    EVENT_WRITE = 4,
    EVENT_TIMEOUT = 5,
};

enum AIOMessageType {
    NONE = 1,
    WAIT_RESPONSE = 2,
    NO_RESPONSE = 3,
};

class AIOData {
public:
    int fd;
    AIOEventType event_type;
    char* buf;
    int buf_size;
    AIOMessageType message_type;
};

class AsyncIO {
public:
    AsyncIO(int message_timeout_ms = 30);

    void set_nonblocking(int sockfd);

    void set_timer(struct io_uring_sqe* sqe);

    void add_timeout(int message_timeout_ms);

    void add_accept_request(int server_socket);

    void add_connect_request(const std::string& ip, int port, WrapperMessage* wrapper_msg, AIOMessageType msg_type);

    void add_read_request(int client_socket);

    void _add_write_request_buf(int client_socket, char* buf, int buf_size, AIOMessageType msg_type);

    void add_write_request_msg(int client_socket, WrapperMessage* wrapper_msg, AIOMessageType msg_type);

    struct io_uring ring_;
    int message_timeout_ms_;
};
