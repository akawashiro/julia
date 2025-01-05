#! /bin/bash

set -eux

ROOT_DIR=$(git rev-parse --show-toplevel)
BUILD_DIR=/tmp/julia_build

rm -rf ${BUILD_DIR}
mkdir -p ${BUILD_DIR}

cd ${ROOT_DIR}
strace \
    --output=${BUILD_DIR}/strace.log \
    --trace=execve,execveat,exit,exit_group \
    --follow-forks \
    --string-limit=1000 \
    --absolute-timestamps=format:unix,precision:us \
    make O=${BUILD_DIR} -j 4
