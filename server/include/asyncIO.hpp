#pragma once
#include <liburing.h>
#include <memory>

#include "wrapperMessage.pb.h"

/**
 * AIOEventType - Type of async I/O event.
 */
enum AIOEventType {
    EVENT_ACCEPT = 1, // Accept new socket
    EVENT_CONNECT = 2, // Connect to server
    EVENT_READ = 3, // Read from socket
    EVENT_WRITE = 4, // Write to socket
    EVENT_TIMEOUT = 5, // Timeout
};

/**
 * AIOMessageType - Type of async I/O message.
 */
enum AIOMessageType {
    NONE = 1, // Not a write message
    WAIT_RESPONSE = 2, // Need to wait for response after write, wait for response
    NO_RESPONSE = 3, // No need to wait for response
};

/**
 * AIOData - Metadata of async I/O event.
 */
class AIOData {
public:
    int fd; // Fd of the event
    AIOEventType event_type; // Type of the event
    char* buf; // Buffer containing message
    int buf_size; // Size of buffer
    AIOMessageType message_type; // Type of message
};

/**
 * AsyncIO - Async I/O layer
 */
class AsyncIO {
public:
    /**
     * AsyncIO - Initialization.
     *
     * @param message_timeout_ms timeout of read and write
     */
    AsyncIO(int message_timeout_ms = 30);

    /**
     * set_nonblocking - Set socket fd as non-blocking.
     *
     * @param sockfd
     */
    void set_nonblocking(int sockfd);

    /**
     * set_timer - Set timeout for submit queue entry.
     *
     * @param sqe
     */
    void set_timer(struct io_uring_sqe* sqe);

    /**
     * add_timeout_request - Add timeout event, periodically wakeup.
     *
     * @param message_timeout_ms
     */
    void add_timeout_request(int message_timeout_ms);

    /**
     * add_accept_request - Add accept event waiting for connecting from other server or client.
     *
     * @param server_socket Accept socket
     */
    void add_accept_request(int server_socket);

    /**
     * add_connect_request - Add connect event waiting for accepting from target server or client.
     *
     * @param ip Target ip
     * @param port Target port
     * @param wrapper_msg Protobuf message to send
     * @param msg_type Type of message
     */
    void add_connect_request(const std::string& ip, int port, WrapperMessage* wrapper_msg, AIOMessageType msg_type);

    /**
     * add_read_request - Add read event waiting for writing from client.
     *
     * @param client_socket Client socket
     */
    void add_read_request(int client_socket);

    /**
     * _add_write_request_buf - Add write event to client, message stored in buffer.
     * Internal function only used for write after connecting, or write after message parsing.
     *
     * @param client_socket Client socket to write to
     * @param buf Buffer containing message
     * @param buf_size Size of buffer
     * @param msg_type Type of message
     */
    void _add_write_request_buf(int client_socket, char* buf, int buf_size, AIOMessageType msg_type);

    /**
     * add_write_request_msg - Add write event to client, message stored in protobuf.
     *
     * @param client_socket Client socket to write to
     * @param wrapper_msg Protobuf message
     * @param msg_type Type of message
     */
    void add_write_request_msg(int client_socket, WrapperMessage* wrapper_msg, AIOMessageType msg_type);

    struct io_uring ring_; // io_uring object
    int message_timeout_ms_; // Timeout for reading and writing
};
