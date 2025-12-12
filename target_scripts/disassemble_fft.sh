#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

SCRIPT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

OUT_PATH="$1"
TOOL_PATH="$2"


${TOOL_PATH}/llvm-objdump -r -M no-aliases -d $SCRIPT_ROOT/../fft/build/fft &> ${OUT_PATH}/fft.asm
