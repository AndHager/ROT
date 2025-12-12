#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

SCRIPT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Build Static analysis pass
cd "${SCRIPT_ROOT}/llvm-pass-plugin"
mkdir -p build
cd build
cmake ..
make -j8

cd "${SCRIPT_ROOT}"
