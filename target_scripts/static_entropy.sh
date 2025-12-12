#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOL_PATH="$1"
OUT_DIR="$1"

for file in aha-mont64 edn huffbench nettle-aes qrduino st matmult-int nettle-sha256 statemate crc32 minver nsichneu sglib-combined ud cubic nbody picojpeg slre wikisort;
do
    fqfp=${SCRIPT_ROOT}/../embench-iot/bd/src/${file}/${file}
    /opt/riscv/bin/riscv32-unknown-elf-readelf -S $fqfp &> ${OUT_DIR}/${file}_size.txt
    cd "${OUT_DIR}"
    /opt/riscv/bin/llvm-objcopy -O binary --only-section=.text ${fqfp} ${OUT_DIR}/${file}_text.dmp
    binwalk --high=0.9 --low=0.8 -c -E -J --block=64 ${OUT_DIR}/${file}_text.dmp &> ${OUT_DIR}/${file}_ent.txt
    binwalk --high=0.9 --low=0.8 -c -E --block=64 -N ${OUT_DIR}/${file}_text.dmp &> ${OUT_DIR}/${file}_ent.txt
    cd "${SCRIPT_ROOT}"
    # echo "/opt/riscv/bin/riscv32-unknown-elf-readelf -S $fqfp"
    /opt/riscv/bin/riscv32-unknown-elf-readelf -S $fqfp &> ${OUT_DIR}/${file}_size.txt
done