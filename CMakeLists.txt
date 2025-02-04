cmake_minimum_required(VERSION 3.14)

# Set the project name
project(Raft2PC CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_FLAGS_DEBUG "-g")

# Add C++ executable (RaftServer)
file(GLOB_RECURSE CPP_SOURCES "server/src/*.cpp")
add_executable(RaftServer server/main.cpp ${CPP_SOURCES})

# Include directories
include_directories(server/include)

find_package(OpenSSL REQUIRED)

# Link necessary libraries for network and threading functionality
target_link_libraries(RaftServer ${CMAKE_THREAD_LIBS} ${CMAKE_DL_LIBS} OpenSSL::Crypto)

# Add Python client with virtual environment
add_custom_target(2PCClient ALL
    COMMAND ${CMAKE_COMMAND} -E echo "Setting up Python virtual environment..."
    COMMAND python3 -m venv ${CMAKE_BINARY_DIR}/venv
    COMMAND ${CMAKE_BINARY_DIR}/venv/bin/python -m pip install --upgrade pip
    COMMAND ${CMAKE_BINARY_DIR}/venv/bin/python -m pip install -r ${CMAKE_SOURCE_DIR}/client/requirements.txt
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}/client
    COMMENT "Creating Python virtual environment and installing dependencies"
)

# Custom build target for creating RaftServer executables
add_custom_target(server
    COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR} --target RaftServer
    DEPENDS RaftServer
)

# Custom build target for creating 2PCClient executables
add_custom_target(client
    COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR} --target 2PCClient
    DEPENDS 2PCClient
)

# Custom build target for creating all two executables
add_custom_target(all
    COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR} --target RaftServer
    COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR} --target 2PCClient
    DEPENDS RaftServer 2PCClient
)

# Custom clean target to remove all build files
add_custom_target(cleanup
    COMMAND ${CMAKE_COMMAND} -E remove_directory ${CMAKE_BINARY_DIR}/*
    COMMENT "Cleaning all build files..."
)