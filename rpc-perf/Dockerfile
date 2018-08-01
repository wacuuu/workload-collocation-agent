# Building rpc-perf.
FROM centos:7 AS rpc-perf

ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:$PATH \
    RUST_VERSION=1.26.2

RUN yum install -y gcc git make wget patch

RUN curl https://sh.rustup.rs -sSf | \
    sh -s -- --default-toolchain stable -y

RUN git clone https://github.com/twitter/rpc-perf.git
WORKDIR /rpc-perf
RUN git checkout 8708682a73efae7d91e5d17a9867e7d1c770482f
ADD intel.patch .
RUN git apply intel.patch
RUN cargo build --release

# Builing final container that consists of workloads only.
FROM centos:7

COPY --from=rpc-perf /rpc-perf/target/release/rpc-perf /usr/bin/
COPY --from=rpc-perf /rpc-perf/configs /etc/rpc-perf/
RUN useradd -M rpc-perf
USER rpc-perf

