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
    EVENT_DUMPDATA = 6, // Dump data into file
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
     */
    AsyncIO();

    /**
     * set_nonblocking - Set socket fd as non-blocking.
     *
     * @param sockfd
     */
    void set_nonblocking(int sockfd);

    /**
     * add_dump_data_request - Add data dumping event, periodically wakeup.
     *
     * @param interval_ms
     */
    void add_dump_data_request(int interval_ms);

    /**
     * add_timeout_request - Add timeout event, periodically wakeup.
     *
     * @param message_timeout_ms
     */
    void add_timeout_request(int message_timeout_ms);

    /**
     * add_accept_request - Add accept event waiting for connecting from other server or client.
     *
     * @param server_socket accept socket
     */
    void add_accept_request(int server_socket);

    /**
     * add_connect_request - Add connect event waiting for accepting from target server or client.
     *
     * @param ip target ip
     * @param port target port
     * @param wrapper_msg protobuf message to send
     * @param msg_type type of message
     */
    void add_connect_request(const std::string& ip, int port, WrapperMessage*& wrapper_msg, AIOMessageType msg_type);

    /**
     * add_read_request - Add read event waiting for writing from client.
     *
     * @param client_socket client socket
     */
    void add_read_request(int client_socket);

    /**
     * _add_write_request_buf - Add write event to client, message stored in buffer.
     * Internal function only used for write after connecting, or write after message parsing.
     *
     * @param client_socket client socket to write to
     * @param buf buffer containing message
     * @param buf_size size of buffer
     * @param msg_type type of message
     */
    void _add_write_request_buf(int client_socket, char*& buf, int& buf_size, AIOMessageType msg_type);

    /**
     * add_write_request_msg - Add write event to client, message stored in protobuf.
     *
     * @param client_socket client socket to write to
     * @param wrapper_msg protobuf message
     * @param msg_type type of message
     */
    void add_write_request_msg(int client_socket, WrapperMessage*& wrapper_msg, AIOMessageType msg_type);

    void add_file_write_request(int fd, const std::string& content);

    struct io_uring ring_; // io_uring object
};
