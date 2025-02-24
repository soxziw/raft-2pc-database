#include <sys/wait.h>
#include <csignal>
#include <fcntl.h>
#include <arpa/inet.h>

#include "nlohmann/json.hpp"
#include "aIOServer.hpp"
#include "exit.pb.h"

/**
 * cmd - Only accept exit command to terminate servers.
 * Send exit message to each server.
 *
 * @param server_ip_port_pairs ip and port pairs of servers
 */
void cmd(std::vector<std::vector<std::pair<std::string, int>>> server_ip_port_pairs) {
    char command[20];
    while (true) {
        int result = std::scanf("%19s", command);
        
        if (result != 1) {
            // Clear input buffer if invalid input
            while (std::getchar() != '\n');
            continue;
        }
        
        if (std::strcmp(command, "exit") == 0) {
            // Send exit message to all servers
            for (int cluster_id = 0; cluster_id < server_ip_port_pairs.size(); cluster_id++) {
                for (int index = 0; index < SERVER_NUM_PER_CLUSTER; index++) {
                    int server_id = cluster_id * SERVER_NUM_PER_CLUSTER + index;
                    // Create socket
                    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
                    if (sockfd < 0) {
                        std::printf("\033[31m[Error] Failed to create socket for cluster %d server %d\033[0m\n", 
                            cluster_id, server_id);
                        continue;
                    }

                    // Connect to server
                    struct sockaddr_in servaddr;
                    servaddr.sin_family = AF_INET;
                    servaddr.sin_port = htons(server_ip_port_pairs[cluster_id][index].second);
                    inet_pton(AF_INET, server_ip_port_pairs[cluster_id][index].first.c_str(), &servaddr.sin_addr);

                    if (connect(sockfd, (struct sockaddr*)&servaddr, sizeof(servaddr)) < 0) {
                        std::printf("\033[31m[Error] Failed to connect to cluster %d server %d\033[0m\n",
                            cluster_id, server_id);
                        close(sockfd);
                        continue;
                    }

                    // Create and send exit message
                    WrapperMessage wrapper_msg;
                    Exit* exit = wrapper_msg.mutable_exit();
                    exit->set_clusterid(cluster_id);
                    exit->set_serverid(server_id);

                    std::string msg_str;
                    wrapper_msg.SerializeToString(&msg_str);

                    // Send message
                    send(sockfd, msg_str.c_str(), msg_str.size(), 0);
                    std::printf("Send exit message to %d:%d\n", cluster_id, server_id);

                    close(sockfd);
                }
            }
            break;
        }
        // Clear the newline character after successful command
        while (std::getchar() != '\n');
    }
}

int main(int argc, char* argv[]) {
    std::pair<std::string, int> routing_service_ip_port_pair = {};
    std::vector<std::vector<std::pair<std::string, int>>> server_ip_port_pairs = {};
    int message_timeout_ms = 1000;

    // Read config from config.json
    int fd = open(CONFIG_PATH, O_RDONLY);
    if (fd < 0) {
        std::printf("[Error] Could not open config.json\n");
        return 1;
    }

    // Get file size
    struct stat st;
    fstat(fd, &st);
    size_t file_size = st.st_size;

    // Read file contents
    std::string json_str;
    json_str.resize(file_size);
    read(fd, &json_str[0], file_size);
    close(fd);

    nlohmann::json config = nlohmann::json::parse(json_str);

    // Initialize routing service config
    routing_service_ip_port_pair = {
        config["ROUTING_SERVICE"]["IP"],
        config["ROUTING_SERVICE"]["PORT"]
    };

    // Initialize server configs
    server_ip_port_pairs.resize(config["SERVERS"].size());
    for (size_t i = 0; i < config["SERVERS"].size(); i++) {
        server_ip_port_pairs[i].resize(config["SERVERS"][i].size());
        for (size_t j = 0; j < SERVER_NUM_PER_CLUSTER; j++) {
            server_ip_port_pairs[i][j] = {
                config["SERVERS"][i][j]["IP"],
                config["SERVERS"][i][j]["PORT"]
            };
        }
    }

    // Get message timeout
    message_timeout_ms = config["MESSAGE_TIMEOUT_MS"];
    
    if (argc > 2) {
        int routing_service_port = std::stoi(argv[1]);
        int server_base_port = std::stoi(argv[2]);

        // Update port numbers in _routing_service_ip_port_pair and _server_ip_port_pairs
        routing_service_ip_port_pair.second = routing_service_port;
        for (size_t i = 0; i < server_ip_port_pairs.size(); i++) {
            for (size_t j = 0; j < SERVER_NUM_PER_CLUSTER; j++) {
                server_ip_port_pairs[i][j].second = server_base_port + i * SERVER_NUM_PER_CLUSTER + j;
            }
        }
    }

    // Create server instances for each cluster/server combination
    std::printf("[Init] Creating server instances.\n");
    std::vector<pid_t> server_pids;
    
    // For each cluster
    for (int cluster_id = 0; cluster_id < server_ip_port_pairs.size(); cluster_id++) {
        // For each server in cluster
        for (int index = 0; index < SERVER_NUM_PER_CLUSTER; index++) {
            int server_id = cluster_id * SERVER_NUM_PER_CLUSTER + index;
            pid_t pid = fork();
            if (pid == 0) {
                // Child process: create and run server
                AIOServer server(cluster_id, server_id, routing_service_ip_port_pair, server_ip_port_pairs, message_timeout_ms);
                return 0;
            } else if (pid > 0) {
                // Parent process: store child pid
                server_pids.push_back(pid);
                sleep(1);
            } else {
                std::printf("[Error] Fork failed\n");
                return 1;
            }
        }
    }

    // Wait for command from terminal
    cmd(server_ip_port_pairs);

    // Wait for all server processes to finish
    for (pid_t pid : server_pids) {
        waitpid(pid, nullptr, 0);
    }
    _exit(0);
}