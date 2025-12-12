#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOL_PATH="$1"
OUT_DIR=${SCRIPT_ROOT}/../"$1"
EMBENCH_DIR="${SCRIPT_ROOT}/../embench-iot-2"

for file in aha-mont64 crc32 depthconv edn huffbench matmult-int md5sum nettle-aes nettle-sha256 nsichneu picojpeg qrduino sglib-combined statemate tarfind ud wikisort xgboost;
do
    fqfp=$EMBENCH_DIR/bd/src/${file}/${file}
    ${TOOL_PATH}/riscv32-unknown-elf-readelf -S $fqfp &> ${OUT_DIR}/${file}_size.txt
    cd "${OUT_DIR}"
    ${TOOL_PATH}/llvm-objcopy -O binary --only-section=.text ${fqfp} ${OUT_DIR}/${file}_text.dmp
    binwalk --high=0.9 --low=0.8 -c -E -J ${OUT_DIR}/${file}_text.dmp &> ${OUT_DIR}/${file}_ent.txt
    cd "${SCRIPT_ROOT}"
    # echo "${TOOL_PATH}/riscv32-unknown-elf-readelf -S $fqfp"
    ${TOOL_PATH}/riscv32-unknown-elf-readelf -S $fqfp &> ${OUT_DIR}/${file}_size.txt
done