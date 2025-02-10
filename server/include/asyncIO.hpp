#pragma once
#include <pthread.h>
#include <liburing.h>
#include <vector>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <functional>
#include <memory>
#include <unistd.h>

#include "ioData.hpp"
#include "wrapperMessage.pb.h"

class AsyncIO {
public:
    AsyncIO(int message_timeout_ms = 30);

    ~AsyncIO();

    void async_read(int fd, std::function<void(const WrapperMessage&)> callback);

    void async_write(int fd, const WrapperMessage& wrapper_msg, std::function<void()> callback);

    void masterThreadFunc();

    void workerThreadFunc();

    struct io_uring ring_;
    pthread_t master_thread_;
    std::vector<pthread_t> worker_threads_;
    std::queue<std::function<void()>> task_queue_;
    std::mutex mutex_;
    std::condition_variable cond_var_;
    bool keep_running_;
    int message_timeout_ms_;
    const int num_workers_ = 4;
};
