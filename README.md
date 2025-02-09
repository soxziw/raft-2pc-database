# Raft-2PC-Database

UCSB Advanced Distributed System Final Project

## Motivation

The [Raft algorithm](https://en.wikipedia.org/wiki/Raft_(algorithm)) was first introduced by [Diego Ongaro](https://twitter.com/ongardie) and [John Ousterhout](https://www.stanford.edu/~ouster/) in their 2014 paper, [*In Search of an Understandable Consensus Algorithm (Extended Version)*](https://raft.github.io/raft.pdf). Designed as an alternative to the [Paxos](https://en.wikipedia.org/wiki/Paxos_(computer_science)) family of algorithms, Raft is a consensus algorithm renowned for its simplicity, safety, and fault tolerance. Unlike Paxos, which is often criticized for its complexity and difficulty of implementation, Raft was explicitly designed to be easier to understand and implement while maintaining strong consistency guarantees. It achieves consensus through a **leader-based** approach, where a single leader is elected to manage log replication across a cluster of servers. The algorithm ensures **fault tolerance** by allowing the system to continue operating as long as a majority of servers (a quorum) are available. Raft's clear separation of concerns—leader election, log replication, and safety—has made it a popular choice for distributed systems such as etcd, MongoDB, and CockroachDB.

The [Two-Phase Commit (2PC) protocol](https://en.wikipedia.org/wiki/Two-phase_commit_protocol), on the other hand, is a distributed algorithm that coordinates all participating processes in a [distributed atomic transaction](https://en.wikipedia.org/wiki/Distributed_transaction) to decide whether to commit or abort (roll back) the transaction. Widely used in transaction processing and database systems, 2PC ensures atomicity across distributed operations by dividing the commit process into two phases. In the **first phase (prepare phase)**, the transaction coordinator queries all participating nodes to ensure they are ready to commit. If all nodes agree, the coordinator proceeds to the **second phase (commit phase)**, where it instructs all nodes to finalize the transaction. If any node fails to prepare or commit, the coordinator aborts the transaction, ensuring consistency. While 2PC provides strong guarantees for atomicity, it is not without drawbacks: it can suffer from blocking issues if the coordinator fails, and its synchronous nature can lead to performance bottlenecks in high-latency or large-scale systems. Despite these limitations, 2PC remains a foundational protocol for distributed transactions in systems like distributed databases and message queues.

As Aristotle once said, *“For the things we have to learn before we can do them, we learn by doing them.”* Inspired by this principle, the objective of this project is to implement a fault-tolerant distributed transaction processing system for a simple banking application. 

## Architecture

### Overview

![raft-2pc database overview](https://drive.usercontent.google.com/download?id=101PHRfC38kbFguuEnHePfbtlF7MipEfy)

Servers are partitioned into multiple clusters, with each cluster maintaining a data shard. Each shard is replicated across all servers within its cluster to ensure fault tolerance. The system supports two types of transactions: **intra-shard** and **cross-shard**. Intra-shard transactions access data items within a single shard, while cross-shard transactions involve data items across multiple shards. To handle intra-shard transactions, the Raft protocol is employed, leveraging its strong consistency and fault tolerance for single-shard operations. For cross-shard transactions, the Two-Phase Commit (2PC) protocol is used to coordinate atomic commits across multiple shards, ensuring that all participating shards either commit or abort the transaction as a single unit. This combination of Raft and 2PC provides a robust foundation for building scalable and reliable distributed systems.

### Intra-Shard transactions - Raft

![intra-shard raft normal operation](https://drive.usercontent.google.com/download?id=1sE7kbGWtmdegO2Z_n_V5E5R0Un3ixXv1)

In normal operation with existing leader, the leader is known by routing service via heartbeat. The routing service redirects IntraShardReq to the leader and wait to heard response from leader. The heartbeat also used to keep other servers in the same cluster from time-out to stay in the same term.

![intra-shard raft leader election](https://drive.usercontent.google.com/download?id=1ZzvF4Tk1DHjQ1bS8iScrjGhSzaLWLKOv)

The routing service is notified elections by RequestVote but not responding to them. When receiving requests in this period of time, routing service keeps requests in its internal queue, until a leader is selected. In upper figure, both S0 and S1 are doing election, and routing service receives vote message from them. Therefore it hang up routing and waiting for the new leader's heartbeat.

### Cross-Shard transactions - 2PC

![cross-shard 2pc prepare phase](https://drive.usercontent.google.com/download?id=1jmWU7jln05lqBIheOJ1N2O33647_GjLb)

For the prepare phase, CrossShardReq(prepare) is only sent to leaders of clusters for them to vote YES or NO.

![cross-shard 2pc commit phase](https://drive.usercontent.google.com/download?id=1Og9ikBCMI4tMsES03ca1gn6dxLwuKDUP)

For the commit phase, CrossShardReq(commit) will be sent to all servers in both clusters.

### Server

![server](https://drive.usercontent.google.com/download?id=1nwliMui-srirz_7m5lhVbefsqt-POBKE)

The io_uring utilizes a **kernel-user space shared submission queue (SQ)** and **completion queue (CQ)** to implement asynchronous input/output (I/O) operations for both socket networking and file access. A **master thread** listens on a specific socket address (IP:port ), awaiting connections from clients or other servers. Upon receiving a message, the master thread assigns the task to a worker from a **thread pool** for further processing. Each worker thread is responsible for managing its own network connections and performing filesystem read/write operations through io_uring, leveraging its asynchronous capabilities to achieve high efficiency and scalability.

### Client

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

## Remote Procedure Call - Protobuf

```protobuf
message WrapperMessage {
  oneof message_type {
    Stop stop = 1;
    Resume resume = 2;
    IntraShardReq intraShardReq = 3;
    IntraShardRsp intraShardRsp = 4;
    CrossShardReq crossShardReq = 5;
    CrossShardRsp crossShardRsp = 6;
    AppendEntriesReq appendEntriesReq = 7;
    AppendEntriesRsp appendEntriesRsp = 8;
    RequestVoteReq requestVoteReq = 9;
    RequestVoteRsp requestVoteRsp = 10;
    PrintBalanceReq printBalanceReq = 11;
    PrintBalanceRsp printBalanceRsp = 12;
    PrintDatastoreReq printDatastoreReq = 13;
    PrintDatastoreRsp printDatastoreRsp = 14;
  }
}
```

### Stop

```protobuf
message Stop {
  required int32 clusterId = 1;
  required int32 serverId = 2;
}
```

### Resume

```protobuf
message Resume {
  required int32 clusterId = 1;
  required int32 serverId = 2;
}
```

### IntraShardReq

```protobuf
message IntraShardReq {
  required int32 clusterId = 1;
  required int32 senderId = 2;
  required int32 receiverId = 3;
  required int32 amount = 4;
  required int32 id = 5;
}
```

### IntraShardRsp

```protobuf
enum IntraShardResultType {
  SUCCESS = 0;
  FAIL = 1;
}

message IntraShardRsp {
  required IntraShardResultType result = 1;
  required int32 id = 2;
}
```

### CrossShardReq

```protobuf
enum CrossShardPhaseType {
  PREPARE = 0;
  COMMIT = 1;
  ABORT = 2;
}

message CrossShardReq {
  required CrossShardPhaseType phase = 1;
  required int32 senderClusterId = 2;
  required int32 receiverClusterId = 3;
  required int32 senderId = 4;
  required int32 receiverId = 5;
  required int32 amount = 6;
  required int32 id = 7;
}
```

### CrossShardRsp

```protobuf
enum CrossShardResultType {
  YES = 0; // Prepare phase
  NO = 1; // Prepare phase
  ACK = 2; // Commit/Abort phase
}

message CrossShardRsp {
  required CrossShardResultType result = 1;
  required int32 id = 2;
}
```

### AppendEntriesReq

```protobuf
message AppendEntriesReq {
  required int32 candidateId = 1; // Candidate requesting vote
  required int32 term = 2; // Candidate's term
  required int32 lastLogIndex = 3; // Index of candidate's last log entry
  required int32 lastLogTerm = 4; // Term of candidate's last log entry
}
```

### AppendEntriesRsp

```protobuf
message AppendEntriesRsp {
  required int32 term = 1; // CurrentTerm, for candidate to update itself
  required bool voteGranted = 2; // True means candidate received vote
}
```

### RequestVoteReq

```protobuf
message LogEntry {
  required int32 term = 1;   // Term when entry was received by leader
  required int32 index = 2;   // Position of entry in the log
  required string command = 3; // Command for state machine
}

message RequestVoteReq {
  required int32 term = 1; // Leader's term
  required int32 leaderId = 2; // So follower can redirect clients
  required int32 prevLogIndex = 3; // Index of log entry immediately preceding new ones
  required int32 prevLogTerm = 4; // Term of prevLogIndex entry
  repeated LogEntry entries = 5; // Log entries to store (empty for heartbeat)
  required int32 commitIndex = 6; // Last entry known to be committed
}
```

### RequestVoteRsp

```protobuf
message RequestVoteRsp {
  required int32 term = 1; // CurrentTerm, for leader to update itself
  required bool success = 2; // True if follower contained entry matching prevLogIndex and prevLogTerm
}
```

### PrintBalanceReq

```protobuf
message PrintBalanceReq {
  required int32 clusterId = 1;
  required int32 serverId = 2;
  required int32 dataItemID = 3;
}
```

### PrintBalanceRsp

```protobuf
message PrintBalanceRsp {
  required int32 clusterId = 1;
  required int32 serverId = 2;
  required int32 dataItemID = 3;
  required int32 balance = 4;
}
```

### PrintDatastoreReq

```protobuf
message PrintDatastoreReq {
  required int32 clusterId = 1;
  required int32 serverId = 2;
}
```

### PrintDatastoreRsp

```protobuf
message PrintDatastoreRsp {
  required int32 clusterId = 1;
  required int32 serverId = 2;
  repeated LogEntry entries = 3;
}
```
