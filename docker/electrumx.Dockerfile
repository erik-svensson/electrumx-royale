FROM python:3.7-alpine3.11

RUN apk add --no-cache build-base openssl \
    && apk add --no-cache --repository http://dl-cdn.alpinelinux.org/alpine/v3.11/main leveldb-dev \
    && apk add --no-cache --repository http://dl-cdn.alpinelinux.org/alpine/edge/testing rocksdb-dev

RUN apk add --no-cache git python3-dev libressl-dev openssl

COPY requirements.txt ./
RUN pip install -r requirements.txt

RUN mkdir /data
ENV HOME /data
ENV ALLOW_ROOT 0
ENV DB_DIRECTORY /data
ENV SERVICES=tcp://:50001,ssl://:50002,wss://:50004,rpc://0.0.0.0:10000
ENV SSL_CERTFILE ${DB_DIRECTORY}/electrumx.crt
ENV SSL_KEYFILE ${DB_DIRECTORY}/electrumx.key
ENV HOST ""
ENV USE_MAX_VERSION 0

RUN openssl req -x509 -nodes -days 365 -subj "/C=US/ST=/O=Minebest/CN=minebest.com"  -newkey rsa:2048 -keyout ${DB_DIRECTORY}/electrumx.key -out ${DB_DIRECTORY}/electrumx.crt

EXPOSE 50001 50002 50004 10000
