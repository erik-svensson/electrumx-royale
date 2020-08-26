FROM ubuntu:18.04 AS builder

RUN apt-get update && \
    apt-get -y install --no-install-recommends --no-install-suggests \
    build-essential \
    curl \
    unzip \
    libboost-all-dev \
    libevent-dev \
    libssl-dev \
    libzmq3-dev \
    pkg-config \
    git \
    unzip \
    autoconf \
    automake \
    libtool
RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:bitcoin/bitcoin
RUN apt-get update && apt-get -y install libdb4.8-dev libdb4.8++-dev

WORKDIR /source
RUN curl -L -k -f  https://github.com/bitcoinvault/bitcoinvault/archive/dev.zip -o dev.zip
RUN unzip dev.zip
RUN rm dev.zip
WORKDIR /source/bitcoinvault-dev
RUN env CFLAGS=-O2 CXXFLAGS=-O2 ./autogen.sh
RUN ./configure --disable-hardening --enable-debug --without-gui --disable-tests --disable-gui-tests --disable-bench
RUN make -j`nproc` && make install

FROM ubuntu:18.04

COPY --from=builder /source/bitcoinvault-dev/src/bvaultd /bvaultd
COPY --from=builder /source/bitcoinvault-dev/src/bvault-cli /bvault-cli
COPY --from=builder /source/bitcoinvault-dev/src/bitcoin-wallet /bitcoin-wallet
COPY --from=builder /source/bitcoinvault-dev/src/bitcoin-tx /bitcoin-tx

RUN apt-get update && \
    apt-get -y install --no-install-recommends --no-install-suggests \
    libboost-all-dev libevent-dev libssl-dev libzmq3-dev
RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:bitcoin/bitcoin
RUN apt-get update && apt-get -y install libdb4.8-dev libdb4.8++-dev

WORKDIR /

RUN mkdir -p /bitcoin

# logrotate
COPY docker/bitcoind-logrotate /etc/logrotate.d/bitcoind
COPY docker/bitcoind-regtest.conf /bitcoin/

EXPOSE 8332 18444

ENTRYPOINT ["./bvaultd","-conf=/bitcoin/bitcoind-regtest.conf"]


