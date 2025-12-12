#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

SCRIPT_ROOT="$(dirname "$(realpath "$0")")"

TOOL_PATH="$1"
OUT_PATH="$2"

EMBENCH_DIR="${SCRIPT_ROOT}/../embench-iot"

# /home/<USER>/Desktop/CodeComp/integrator/hardware_base/obj_dir/Vtb_top_verilator +firmware=/home/<USER>/Desktop/CodeComp/integrator/firmware/build/firmware.mem +verbose

LAST_PID="-1"
LAST_NAME=""

for file in $(ls $EMBENCH_DIR/src); do

  file_dir=$EMBENCH_DIR/bd/src/${file}

  ${TOOL_PATH}/llvm-objdump -r -M no-aliases -d $file_dir/${file} &>${OUT_PATH}/${file}.asm_cv32e40x
  # hardware_base

  EXIT_CODE=0
  (
    set -x
    $SCRIPT_ROOT/../hardware/obj_dir/Vtb_top_verilator +firmware=$file_dir/firmware.mem +verbose &>${OUT_PATH}/${file}_core_trace.txt || EXIT_CODE=$?
    mv $SCRIPT_ROOT/../trace.fst ${OUT_PATH}/${file}.fst
  )
  echo "Exit code: $EXIT_CODE"
  # mv $SCRIPT_ROOT/../db/results.db ${OUT_PATH}/${file}_results.db

  # if [ "$LAST_PID" != "-1" ] ; then
  #     wait $LAST_PID
  #     rm $LAST_NAME
  # fi
  # LAST_NAME=${SCRIPT_ROOT}/../out/${file}.fst
  # bzip3 -f -j10 $LAST_NAME &
  # LAST_PID=$!
done
