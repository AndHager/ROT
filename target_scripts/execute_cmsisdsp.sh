#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

SCRIPT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

for file in example;
do 
    echo "  INFO Executing: $SCRIPT_ROOT/../riscv-isa-sim/build/spike -l $SCRIPT_ROOT/../riscv-isa-sim/riscv-pk/build/pk ${SCRIPT_ROOT}/../cmsis-dsp-riscv/build-riscv/build/${file}"
    $SCRIPT_ROOT/../riscv-isa-sim/build/spike -l $SCRIPT_ROOT/../riscv-isa-sim/riscv-pk/build/pk ${SCRIPT_ROOT}/../cmsis-dsp-riscv/build-riscv/build/${file} &> ${SCRIPT_ROOT}/../out/${file}_trace.txt || true
done
