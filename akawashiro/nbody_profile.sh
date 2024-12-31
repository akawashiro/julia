#! /bin/bash

set -eux -o pipefail

ROOT_DIR=$(git rev-parse --show-toplevel)
FLAMEGRAPH_DIR=/tmp/FlameGraph
SCRIPT_DIR=$(realpath $(dirname "$0"))

if [ -d ${FLAMEGRAPH_DIR} ]; then
    echo "FlameGraph already exists"
else
    git clone https://github.com/brendangregg/FlameGraph ${FLAMEGRAPH_DIR}
fi

# Profile julia with JIT compile
ENABLE_JITPROFILING=1 perf record -F 99 -a --call-graph dwarf -k 1 -o ${SCRIPT_DIR}/nbody.profile -- time ./julia ${SCRIPT_DIR}/nbody.jl
perf inject --jit --input ${SCRIPT_DIR}/nbody.profile --output ${SCRIPT_DIR}/nbody.jit.profile
perf script --input ${SCRIPT_DIR}/nbody.jit.profile | ${FLAMEGRAPH_DIR}/stackcollapse-perf.pl > ${SCRIPT_DIR}/nbody.perf-folded
${FLAMEGRAPH_DIR}/flamegraph.pl ${SCRIPT_DIR}/nbody.perf-folded > ${SCRIPT_DIR}/nbody.svg

# Profile julia without JIT compile
# Run on CPU #0
perf record \
    -F 99 \
    --cpu 0 \
    --call-graph dwarf \
    -o ${SCRIPT_DIR}/nbody_compile_no.profile \
    -- taskset -c 0 \
        ${ROOT_DIR}/julia \
            --compile=no \
            --compiled-modules=no \
            ${SCRIPT_DIR}/nbody.jl

perf script \
    --input ${SCRIPT_DIR}/nbody_compile_no.profile | \
    ${SCRIPT_DIR}/FlameGraph/stackcollapse-perf.pl > ${SCRIPT_DIR}/nbody_compile_no.perf-folded
${FLAMEGRAPH_DIR}/flamegraph.pl ${SCRIPT_DIR}/nbody_compile_no.perf-folded > ${SCRIPT_DIR}/nbody_compile_no.svg
