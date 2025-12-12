#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

SCRIPT_ROOT="$(dirname "$(realpath "$0")")"
EMBENCH_DIR="${SCRIPT_ROOT}/../embench-iot-2"

for file in aha-mont64 crc32 depthconv edn huffbench matmult-int md5sum nettle-aes nettle-sha256 nsichneu picojpeg qrduino sglib-combined statemate tarfind ud wikisort xgboost; do
  EXIT_CODE=0
  (
    set -x
    $SCRIPT_ROOT/../riscv-isa-sim/build/spike -m1024 --isa=rv32imafczicntr_zcmp -l $SCRIPT_ROOT/../riscv-isa-sim/riscv-pk/build/pk $EMBENCH_DIR/bd/src/${file}/${file} &>$SCRIPT_ROOT/../out/${file}_trace.txt || EXIT_CODE=$?
  )
  echo "Exit code: $EXIT_CODE"
done
