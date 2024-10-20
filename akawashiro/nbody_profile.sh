#! /bin/bash

set -eux -o pipefail
root_dir=$(git rev-parse --show-toplevel)

cd ${root_dir}

if [ -d akawashiro/FlameGraph ]; then
    echo "FlameGraph already exists"
else
    git clone https://github.com/brendangregg/FlameGraph akawashiro/FlameGraph
fi

ENABLE_JITPROFILING=1 perf record -F 99 -a --call-graph dwarf -k 1 -o akawashiro/nbody.profile -- time ./julia akawashiro/nbody.jl
perf inject --jit --input akawashiro/nbody.profile --output akawashiro/nbody.jit.profile
perf script --input akawashiro/nbody.jit.profile | akawashiro/FlameGraph/stackcollapse-perf.pl > akawashiro/nbody.perf-folded
./akawashiro/FlameGraph/flamegraph.pl akawashiro/nbody.perf-folded > akawashiro/nbody.svg

perf record -F 99 -a --call-graph dwarf -k 1 -o akawashiro/nbody_compile_no.profile -- time ${root_dir}/julia --compile=no --compiled-modules=no akawashiro/nbody.jl
perf script --input akawashiro/nbody_compile_no.profile | akawashiro/FlameGraph/stackcollapse-perf.pl > akawashiro/nbody_compile_no.perf-folded
./akawashiro/FlameGraph/flamegraph.pl akawashiro/nbody_compile_no.perf-folded > akawashiro/nbody_compile_no.svg
