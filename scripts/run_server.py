#!/usr/bin/env python3
import os
import sys
import subprocess

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    server_executable = os.path.join(script_dir, "../build/RaftServer")

    if not os.path.exists(server_executable):
        print(f"Error: Server executable not found at {server_executable}")
        print("Please run 'cmake --build server' first to build raft server")
        sys.exit(1)

    try:
        print("Running raft server...")
        subprocess.run(server_executable, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running {server_executable}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()