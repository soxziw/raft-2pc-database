#!/usr/bin/env python3
import os
import sys
import subprocess

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(script_dir, "build/venv/bin/python")
    client_script = os.path.join(script_dir, "client/client.py")

    if not os.path.exists(venv_python):
        print(f"Error: Virtual environment not found at {venv_python}")
        print("Please run 'cmake --build build' first to create the virtual environment")
        sys.exit(1)

    try:
        print("Activating virtual environment and running script...")
        subprocess.run([venv_python, client_script], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running {client_script}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()