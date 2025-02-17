cmake_minimum_required(VERSION 3.14)

# Set the project name
project(Raft2PC CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_CXX_FLAGS_DEBUG "-g")

if(BUILD_SERVER)
    # Find packages for server
    find_package(Protobuf REQUIRED)
    find_package(PkgConfig REQUIRED)
    find_package(fmt REQUIRED)
    pkg_check_modules(LIBURING REQUIRED liburing)

    add_definitions(-DCONFIG_PATH="${CMAKE_SOURCE_DIR}/config.json")

    # Set proto files
    file(GLOB PROTO_FILES "${CMAKE_SOURCE_DIR}/proto/*.proto")

    # Generate protobuf sources
    protobuf_generate_cpp(PROTO_SRCS PROTO_HDRS ${PROTO_FILES})

    # Mark generated files as GENERATED
    set_source_files_properties(${PROTO_SRCS} PROPERTIES GENERATED TRUE)
    set_source_files_properties(${PROTO_HDRS} PROPERTIES GENERATED TRUE)

    # Add C++ executable (RaftServer)
    file(GLOB_RECURSE CPP_SOURCES "server/src/*.cpp")
    add_executable(RaftServer server/main.cpp ${CPP_SOURCES} ${PROTO_SRCS})

    # Include directories
    target_include_directories(RaftServer PRIVATE ${CMAKE_CURRENT_BINARY_DIR} ${LIBURING_INCLUDE_DIRS} server/include)

    # Link necessary libraries for network and threading functionality
    target_link_libraries(RaftServer PRIVATE protobuf::libprotobuf ${LIBURING_LIBRARIES} fmt::fmt)

    # Custom build target for creating RaftServer executables
    add_custom_target(server
        COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR} --target RaftServer
        DEPENDS RaftServer
    )
endif()

if(BUILD_CLIENT)
    # Find protobuf for client
    find_package(Protobuf REQUIRED)

    add_definitions(-DCONFIG_PATH="${CMAKE_SOURCE_DIR}/config.json")

    # Set proto files
    file(GLOB PROTO_FILES "${CMAKE_SOURCE_DIR}/proto/*.proto")

    # Add Python client with virtual environment
    add_custom_target(2PCClient ALL
        COMMAND ${CMAKE_COMMAND} -E echo "Setting up Python virtual environment..."
        COMMAND python3 -m venv ${CMAKE_BINARY_DIR}/venv
        COMMAND ${CMAKE_BINARY_DIR}/venv/bin/python -m pip install --upgrade pip
        COMMAND ${CMAKE_BINARY_DIR}/venv/bin/python -m pip install -r ${CMAKE_SOURCE_DIR}/client/requirements.txt
        WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}/client
        COMMENT "Creating Python virtual environment and installing dependencies"
    )

    # Generate Python protobuf files
    add_custom_command(
        OUTPUT python_proto
        COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_SOURCE_DIR}/client/proto
        COMMAND ${PROTOBUF_PROTOC_EXECUTABLE}
            --python_out=${CMAKE_SOURCE_DIR}/client/proto
            --proto_path=${CMAKE_SOURCE_DIR}/proto
            ${PROTO_FILES}
        DEPENDS ${PROTO_FILES}
        COMMENT "Generating Python protocol buffers..."
    )
    add_custom_target(generate_python_proto ALL DEPENDS python_proto)

    # Make 2PCClient depend on Python proto generation
    add_dependencies(2PCClient generate_python_proto)

    # Custom build target for creating 2PCClient executables
    add_custom_target(client
        COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR} --target 2PCClient
        DEPENDS 2PCClient
    )
endif()

# Custom build target for creating all two executables
add_custom_target(raft2pc
    COMMAND ${CMAKE_COMMAND} -DBUILD_SERVER=ON -DBUILD_CLIENT=ON -B ${CMAKE_BINARY_DIR}/all -S ${CMAKE_SOURCE_DIR}
    COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR}/all --target server
    COMMAND ${CMAKE_COMMAND} --build ${CMAKE_BINARY_DIR}/all --target client
)

# Custom clean target to remove all build files
add_custom_target(cleanup
    COMMAND ${CMAKE_COMMAND} -E remove_directory ${CMAKE_BINARY_DIR}/*
    COMMENT "Cleaning all build files..."
)