.PHONY: client server raft2pc clean

client:
	@mkdir -p build
	@CC=/usr/bin/clang-15 CXX=/usr/bin/clang++-15 cmake -DBUILD_CLIENT=ON -DBUILD_SERVER=OFF -B build -S .
	@make -C build client | grep -vE "make\[[0-9]+\]"

server:
	@mkdir -p build
	@CC=/usr/bin/clang-15 CXX=/usr/bin/clang++-15 cmake -DBUILD_CLIENT=OFF -DBUILD_SERVER=ON -B build -S .
	@make -C build server | grep -vE "make\[[0-9]+\]"

raft2pc:
	@mkdir -p build
	@CC=/usr/bin/clang-15 CXX=/usr/bin/clang++-15 cmake -B build -S .
	@make -C build raft2pc | grep -vE "make\[[0-9]+\]"

clean:
	@mkdir -p build
	@CC=/usr/bin/clang-15 CXX=/usr/bin/clang++-15 cmake -B build -S . > /dev/null 2>&1
	@make -C build cleanup | grep -vE "make\[[0-9]+\]"
	@rm -rf client/proto
	@rm -rf build