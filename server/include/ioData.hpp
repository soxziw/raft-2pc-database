#pragma once
#include <functional>

struct IOData {
    int fd;
    char* buf;
    std::function<void()> callback;
};