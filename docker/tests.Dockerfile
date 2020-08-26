FROM python:3.7-alpine3.11

RUN apk add --no-cache build-base openssl \
    && apk add --no-cache --repository http://dl-cdn.alpinelinux.org/alpine/v3.11/main leveldb-dev \
    && apk add --no-cache --repository http://dl-cdn.alpinelinux.org/alpine/edge/testing rocksdb-dev

RUN apk add --no-cache git python3-dev libressl-dev openssl

COPY requirements.txt ./
RUN pip install -r requirements.txt
