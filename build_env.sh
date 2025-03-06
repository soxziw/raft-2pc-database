#!/bin/bash

# Update package lists and upgrade existing packages
apt update && apt upgrade -y

# Install required development tools and dependencies
apt-get install -y \
    clang-15 \
    git \
    make \
    cmake \
    python3.10 \
    python3.10-venv \
    python3.10-dev \
    libfmt-dev \
    liburing-dev \
    protobuf-compiler \
    libprotobuf-dev