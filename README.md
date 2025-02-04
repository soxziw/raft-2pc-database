# Raft-2PC-Database
UCSB Advanced Distributed System Final Project

## Build
Build client only:
```bash
make client
```

Build server only:
```bash
make server
```

Build both client and server:
```bash
make all
```

Clean everything has been built:
```bash
make clean
```

## Run
Make sure to run after the build.
Run client:
```bash
python3 scripts/run_client.py
```

Run server:
```bash
python3 scripts/run_server.py
```
