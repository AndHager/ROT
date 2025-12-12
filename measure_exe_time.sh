#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

SCRIPT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
OUT_DIR="$1"

cd "${OUT_DIR}"
ASM=$(printf  '%s ' *.etiss_asm)
cd "${SCRIPT_ROOT}"
# echo "Target, InstructionCount, ParseTime, GenerationTime, MergeTime, SelectionTime"
echo "Target,InstructionCount,ParseTime,DynamicInstructionCount,DynamicParseTime,GenerationTime,MergeTime,SelectionTime"

python3 ${SCRIPT_ROOT}/analysis/generator.py --dynamic True --count True --time True --csv True --path ${OUT_DIR} ${ASM}

