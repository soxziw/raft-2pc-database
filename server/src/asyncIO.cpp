#include <chrono>
#include "asyncIO.hpp"


AsyncIO::AsyncIO(int message_timeout_ms) : keep_running_(true), message_timeout_ms_(message_timeout_ms) {
    // Initialize io_uring
    struct io_uring_params params;
    memset(&params, 0, sizeof(params));
    if (io_uring_queue_init_params(32, &ring_, &params) < 0) {
        throw std::runtime_error("Failed to initialize io_uring");
    }

    // Create master thread
    pthread_create(&master_thread_, nullptr, [](void* arg) -> void* {
        AsyncIO* async_io = static_cast<AsyncIO*>(arg);
        async_io->masterThreadFunc();
        return nullptr;
    }, this);

    // Create worker threads
    for (int i = 0; i < num_workers_; ++i) {
        pthread_t worker_thread;
        pthread_create(&worker_thread, nullptr, [](void* arg) -> void* {
            AsyncIO* async_io = static_cast<AsyncIO*>(arg);
            async_io->workerThreadFunc();
            return nullptr;
        }, this);
        worker_threads_.push_back(worker_thread);
    }
}

AsyncIO::~AsyncIO() {
    keep_running_ = false;
    cond_var_.notify_all();
    
    // Join master thread
    pthread_join(master_thread_, nullptr);

    // Join worker threads
    for (auto& worker : worker_threads_) {
        pthread_join(worker, nullptr);
    }
    
    io_uring_queue_exit(&ring_);
}

void AsyncIO::async_read(int fd, std::function<void(const WrapperMessage&)> callback) {
    char* buf = new char[1024];
    IOData* read_data = new IOData{fd, buf, [this, callback, buf, read_data]() {
        WrapperMessage wrapper_msg;
        if (wrapper_msg.ParseFromArray(buf, 1024)) {
            callback(wrapper_msg);
        }
        delete[] buf;
        delete read_data;
    }};

    struct io_uring_sqe* sqe = io_uring_get_sqe(&ring_);
    io_uring_prep_read(sqe, fd, buf, 1024, 0);
    io_uring_sqe_set_data(sqe, read_data);
    
    // Set 30ms timeout
    struct __kernel_timespec ts;
    ts.tv_sec = 0;
    ts.tv_nsec = message_timeout_ms_ * 1000000; // 30ms in nanoseconds
    io_uring_prep_timeout(sqe, &ts, 0, 0);
    
    io_uring_submit(&ring_);
}

void AsyncIO::async_write(int fd, const WrapperMessage& wrapper_msg, std::function<void()> callback) {
    std::string serialized;
    wrapper_msg.SerializeToString(&serialized);
    
    char* buf = new char[serialized.size()];
    memcpy(buf, serialized.data(), serialized.size());
    
    IOData* write_data = new IOData{fd, buf, [this, callback, buf, write_data, fd]() {
        callback();
        close(fd);
        delete[] buf;
        delete write_data;
    }};

    struct io_uring_sqe* sqe = io_uring_get_sqe(&ring_);
    io_uring_prep_write(sqe, fd, buf, serialized.size(), 0);
    io_uring_sqe_set_data(sqe, write_data);
    
    // Set 30ms timeout
    struct __kernel_timespec ts;
    ts.tv_sec = 0;
    ts.tv_nsec = message_timeout_ms_ * 1000000; // 30ms in nanoseconds
    io_uring_prep_timeout(sqe, &ts, 0, 0);

    io_uring_submit(&ring_);
}

void AsyncIO::masterThreadFunc() {
    while (keep_running_) {
        struct io_uring_cqe* cqe;
        int ret = io_uring_wait_cqe(&ring_, &cqe);
        if (ret < 0) continue;

        IOData* completed_data = (IOData*)io_uring_cqe_get_data(cqe);
        int res = cqe->res;
        io_uring_cqe_seen(&ring_, cqe);
        if (completed_data && completed_data->callback) {
            std::unique_lock<std::mutex> lock(mutex_);
            task_queue_.emplace([completed_data]() {
                completed_data->callback();
            });
            cond_var_.notify_one();
        }
    }
}

void AsyncIO::workerThreadFunc() {
    while (keep_running_) {
        std::function<void()> task;
        {
            std::unique_lock<std::mutex> lock(mutex_);
            cond_var_.wait(lock, [this]() {
                return !task_queue_.empty() || !keep_running_;
            });
            if (!keep_running_) break;
            task = std::move(task_queue_.front());
            task_queue_.pop();
        }
        task();
    }
}