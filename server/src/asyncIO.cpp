#include <liburing.h>
#include <memory>
#include <arpa/inet.h>
#include <fcntl.h>
#include <unistd.h>
#include <fmt/format.h>

#include "asyncIO.hpp"
#include "utils.hpp"

AsyncIO::AsyncIO() {
    // Init
    struct io_uring_params params;
    memset(&params, 0, sizeof(params));
    if (io_uring_queue_init_params(1024, &ring_, &params) < 0) {
        fatal_error("Init io_uring error.");
    }
};

void AsyncIO::set_nonblocking(int sockfd) {
    // Set non-blocking
    int flags = fcntl(sockfd, F_GETFL, 0);
    fcntl(sockfd, F_SETFL, flags | O_NONBLOCK);
}

void AsyncIO::add_dump_data_request(int interval_s) {
    // Generate timeout metadata
    AIOData* data = new AIOData{0, AIOEventType::EVENT_DUMPDATA, nullptr, 0, AIOMessageType::NONE};
    struct io_uring_sqe* sqe = io_uring_get_sqe(&ring_);
    struct __kernel_timespec ts;
    ts.tv_sec = interval_s;
    ts.tv_nsec = 0;
    io_uring_prep_timeout(sqe, &ts, 0, 0);
    io_uring_sqe_set_data(sqe, data);

    int ret = io_uring_submit(&ring_);
    if (ret < 0) {
        delete data;
        fatal_error("Failed to submit io_uring request.");
    }
}

void AsyncIO::add_timeout_request(int message_timeout_ms) {
    // Generate timeout metadata
    AIOData* data = new AIOData{0, AIOEventType::EVENT_TIMEOUT, nullptr, 0, AIOMessageType::NONE};
    struct io_uring_sqe* sqe = io_uring_get_sqe(&ring_);
    struct __kernel_timespec ts;
    ts.tv_sec = message_timeout_ms / 1000;
    ts.tv_nsec = (message_timeout_ms % 1000) * 1000000;
    io_uring_prep_timeout(sqe, &ts, 0, 0);
    io_uring_sqe_set_data(sqe, data);

    int ret = io_uring_submit(&ring_);
    if (ret < 0) {
        delete data;
        fatal_error("Failed to submit io_uring request.");
    }
}

void AsyncIO::add_accept_request(int server_socket) {
    // Generate accept metadata
    AIOData* data = new AIOData{server_socket, AIOEventType::EVENT_ACCEPT, nullptr, 0, AIOMessageType::NONE};
    struct io_uring_sqe* sqe = io_uring_get_sqe(&ring_);
    io_uring_prep_accept(sqe, server_socket, nullptr, nullptr, 0);
    io_uring_sqe_set_data(sqe, data);
    int ret = io_uring_submit(&ring_);
    if (ret < 0) {
        delete data;
        fatal_error("Failed to submit io_uring request.");
    }
}

void AsyncIO::add_connect_request(const std::string& ip, int port, WrapperMessage*& wrapper_msg, AIOMessageType msg_type) {
    int client_socket;
    struct sockaddr_in clt_addr;

    client_socket = socket(PF_INET, SOCK_STREAM, 0);
    set_nonblocking(client_socket);

    memset(&clt_addr, 0, sizeof(clt_addr));
    clt_addr.sin_family = AF_INET;
    clt_addr.sin_port = htons(port);
    inet_pton(AF_INET, ip.c_str(), &clt_addr.sin_addr);

    char* buf;
    int buf_size;
    serialize_msg_to_buf(wrapper_msg, buf, buf_size);

    // Generate connect metadata
    AIOData* data = new AIOData{client_socket, AIOEventType::EVENT_CONNECT, buf, buf_size, msg_type};

    struct io_uring_sqe* sqe = io_uring_get_sqe(&ring_);
    io_uring_prep_connect(sqe, client_socket, (struct sockaddr *)&clt_addr, sizeof(clt_addr));
    io_uring_sqe_set_data(sqe, data);
    int ret = io_uring_submit(&ring_);
    if (ret < 0) {
        delete data;
        fatal_error("Failed to submit io_uring request.");
    }
}

void AsyncIO::add_read_request(int client_socket) {

    set_nonblocking(client_socket);

    char* buf = new char[1024]{};

    // Generate read metadata
    AIOData* data = new AIOData{client_socket, AIOEventType::EVENT_READ, buf, 1024, AIOMessageType::NONE};
    struct io_uring_sqe* sqe = io_uring_get_sqe(&ring_);
    io_uring_prep_read(sqe, client_socket, buf, 1024, 0);
    io_uring_sqe_set_data(sqe, data);

    int ret = io_uring_submit(&ring_);
    if (ret < 0) {
        delete[] buf;
        delete data;
        fatal_error("Failed to submit io_uring request.");
    }
}

void AsyncIO::_add_write_request_buf(int client_socket, char*& buf, int& buf_size, AIOMessageType msg_type) {

    set_nonblocking(client_socket);

    // Generate write metadata
    AIOData* data = new AIOData{client_socket, AIOEventType::EVENT_WRITE, buf, buf_size, msg_type};
    struct io_uring_sqe* sqe = io_uring_get_sqe(&ring_);
    io_uring_prep_write(sqe, client_socket, buf, buf_size, 0);
    io_uring_sqe_set_data(sqe, data);

    int ret = io_uring_submit(&ring_);
    if (ret < 0) {
        delete data;
        fatal_error("Failed to submit io_uring request.");
    }
}

void AsyncIO::add_write_request_msg(int client_socket, WrapperMessage*& wrapper_msg, AIOMessageType msg_type) {
    char* buf;
    int buf_size;
    serialize_msg_to_buf(wrapper_msg, buf, buf_size);

    _add_write_request_buf(client_socket, buf, buf_size, msg_type);
}

void AsyncIO::add_file_write_request(int fd, const std::string& content) {
    // Create a buffer with the content
    char* buf = new char[content.length()];
    memcpy(buf, content.c_str(), content.length());
    
    // Generate write metadata
    AIOData* data = new AIOData{fd, AIOEventType::EVENT_WRITE, buf, static_cast<int>(content.length()), AIOMessageType::NONE};

    // Prepare and submit the write request
    struct io_uring_sqe* sqe = io_uring_get_sqe(&ring_);
    io_uring_prep_write(sqe, fd, buf, content.length(), 0);
    io_uring_sqe_set_data(sqe, data);

    int ret = io_uring_submit(&ring_);
    if (ret < 0) {
        delete[] buf;
        delete data;
        fatal_error("Failed to submit io_uring file write request.");
    }
}