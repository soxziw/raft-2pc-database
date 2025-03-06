#include <cerrno>
#include <cstdlib>
#include <memory>
#include <filesystem>
#include <fcntl.h>
#include <fmt/format.h>
#include <string>
#include <sys/stat.h>
#include <unistd.h>

#include "nlohmann/json.hpp"
#include "utils.hpp"

void fatal_error(const std::string& str) {
    perror(("[ERROR] " + str).c_str());
    exit(1);
}

void load_data_shard(std::shared_ptr<RaftState> raft_state) {
    std::printf("[%d:%d] Load data shard.\n", raft_state->cluster_id_, raft_state->server_id_);
    // Open data shard file with read only permission
    std::filesystem::path file_path = std::filesystem::path(DATA_SHARD_BASE) / ("dataShard" + std::to_string(raft_state->cluster_id_) + ".jsonl");
    int fd = open(file_path.c_str(), O_RDONLY);
    struct stat file_stat;
    if (fstat(fd, &file_stat) == -1) {
        close(fd);
        return;
    }

    // Read whole file into buffer
    off_t file_size = file_stat.st_size;
    std::vector<char> buffer(file_size);
    ssize_t bytes_read = read(fd, buffer.data(), file_size);
    if (bytes_read == -1) {
        close(fd);
        return;
    }

    // Split buffer into lines
    size_t start = 0;
    for (size_t i = 0; i < bytes_read; ++i) {
        if (buffer[i] == '\n') {
            raft_state->balance_jsonl_.push_back(std::string(buffer.begin() + start, buffer.begin() + i));
            start = i + 1;
        }
    }
    if (start < bytes_read) {
        raft_state->balance_jsonl_.push_back(std::string(buffer.begin() + start, buffer.begin() + bytes_read));
    }

    // Load data items into local balance table
    for (const auto& line : raft_state->balance_jsonl_) {
        try {
            nlohmann::json j = nlohmann::json::parse(line);
            int id = j["id"];
            int balance = j["units"];
            raft_state->local_balance_tb_[id] = balance;
        } catch (const nlohmann::json::exception& e) {
            std::printf("%s", fmt::format("nlohmann::json parsing error: {}\n", e.what()).c_str());
            continue;
        }
    }

    // Close file descriptor
    close(fd);
}

void update_data_shard(std::shared_ptr<RaftState> raft_state, std::shared_ptr<AsyncIO> aio) {
    if (raft_state->modify_items_.empty()) {
        return;
    }
    
    std::printf("[%d:%d] Update data shard.\n", raft_state->cluster_id_, raft_state->server_id_);
    // Open data shard file with read only permission
    std::filesystem::path file_path = std::filesystem::path(DATA_SHARD_BASE) / ("dataShard" + std::to_string(raft_state->cluster_id_) + ".jsonl");
    int fd = open(file_path.c_str(), O_RDWR);

    // Update balance of each data items
    for (const auto& item_id : raft_state->modify_items_) {
        try {
            nlohmann::json j = nlohmann::json::parse(raft_state->balance_jsonl_[item_id - 1]);
            j["units"] = raft_state->local_balance_tb_[item_id];
            // Convert the updated JSON back to string and replace the line
            raft_state->balance_jsonl_[item_id - 1] = j.dump();
        } catch (const nlohmann::json::exception& e) {
            std::printf("%s", fmt::format("nlohmann::json parsing error: {}\n", e.what()).c_str());
            continue;
        }
    }

    // Truncate original content
    if (ftruncate(fd, 0) == -1) {
        close(fd);
        return;
    }
    lseek(fd, 0, SEEK_SET);

    // Write all lines at once using io_uring
    std::string all_content;
    for (const auto& line : raft_state->balance_jsonl_) {
        all_content += line + "\n";
    }
    
    aio->add_file_write_request(fd, all_content);
    raft_state->modify_items_.clear();
}

void serialize_msg_to_buf(WrapperMessage*& wrapper_msg, char*& buf, int& buf_size) {
    // Serialize and delete message object
    std::string serialized;
    wrapper_msg->SerializeToString(&serialized);
    delete wrapper_msg;
    // Create and fill buffer object
    buf = new char[serialized.size()];
    memcpy(buf, serialized.data(), serialized.size());
    buf_size = serialized.size();
}

void parse_buf_to_msg(WrapperMessage*& wrapper_msg, char*& buf, int& buf_size) {
    // Create and parse message object
    wrapper_msg = new WrapperMessage;
    wrapper_msg->ParseFromArray(buf, buf_size);

    // Delete buffer object
    delete[] buf;
}