#! /bin/bash

set -eux -o pipefail

root_dir=$(git rev-parse --show-toplevel)
FLAMEGRAPH_DIR=/tmp/FlameGraph
cd $root_dir

if [ -d ${FLAMEGRAPH_DIR} ]; then
    echo "FlameGraph already exists"
else
    git clone https://github.com/brendangregg/FlameGraph ${FLAMEGRAPH_DIR}
fi

ENABLE_JITPROFILING=1 perf record -F 99 -a --call-graph dwarf -k 1 -o akawashiro/lorenz.profile -- time ./julia akawashiro/lorenz.jl
perf inject --jit --input akawashiro/lorenz.profile --output akawashiro/lorenz.jit.profile
perf script --input akawashiro/lorenz.jit.profile | ${FLAMEGRAPH_DIR}/stackcollapse-perf.pl > akawashiro/lorenz.perf-folded
${FLAMEGRAPH_DIR}/flamegraph.pl akawashiro/lorenz.perf-folded > akawashiro/lorenz.svg

perf record -F 99 -a --call-graph dwarf -k 1 -o akawashiro/lorenz_compile_no.profile -- time ./julia --compile=no akawashiro/lorenz.jl
perf script --input akawashiro/lorenz_compile_no.profile | ${FLAMEGRAPH_DIR}/stackcollapse-perf.pl > akawashiro/lorenz_compile_no.perf-folded
${FLAMEGRAPH_DIR}/flamegraph.pl akawashiro/lorenz_compile_no.perf-folded > akawashiro/lorenz_compile_no.svg
