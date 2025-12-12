#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

SCRIPT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

OUT_PATH="$1"
TOOL_PATH="$2"

EMBENCH_DIR="${SCRIPT_ROOT}/../embench-iot"

for file in aha-mont64 crc32 cubic edn huffbench matmult-int md5sum minver nbody nettle-aes nettle-sha256 nsichneu picojpeg primecount qrduino sglib-combined slre st statemate tarfind ud wikisort;
do 
    #echo "  INFO Executing: ${TOOL_PATH}/llvm-objdump -d ${SCRIPT_ROOT}/embench-iot/bd/install/bin/${file} &> ${SCRIPT_ROOT}/out/${file}.rv32"
   
    # ${TOOL_PATH}/llvm-objdump -r -M no-aliases -d $EMBENCH_DIR/bd/src/${file}/${file} &> ${OUT_PATH}/${file}.asm
    ${TOOL_PATH}/llvm-objdump -r -M no-aliases -d $EMBENCH_DIR/bd/install/bin/${file} &> ${OUT_PATH}/${file}.etiss_asm
done
