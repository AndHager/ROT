#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

SCRIPT_ROOT="$(dirname "$(realpath "$0")")"

TOOL_PATH="$1"
OUT_PATH="$2"

# TOOL_PATH="~/Desktop/CodeComp"

mkdir -p $OUT_PATH/power
cp -r -f $SCRIPT_ROOT/../res/power $OUT_PATH

cd "${OUT_PATH}"

for file in aha-mont64 crc32 depthconv edn huffbench matmult-int md5sum nettle-aes nettle-sha256 nsichneu picojpeg qrduino sglib-combined statemate tarfind ud wikisort xgboost; do

  echo "Processing: $file"

  cp -f ${OUT_PATH}/power/sta.tcl ${OUT_PATH}/${file}_sta.tcl
  # Warning: This does not consider newlines.
  ESCAPED_REPLACE=$(printf '%s\n' "$OUT_PATH" | sed -e 's/[\/&]/\\&/g')
  sed -i "s/<OUT_DIR>/${ESCAPED_REPLACE}/g" ${OUT_PATH}/${file}_sta.tcl
  sed -i "s/<TRACE_TCL>/${file}/g" ${OUT_PATH}/${file}_sta.tcl

  $TOOL_PATH/trace2power/target/release/trace2power --clk-freq 10000000 -f tcl -o ${OUT_PATH}/$file.tcl ${OUT_PATH}/$file.fst
  $TOOL_PATH/OpenSTA/build/sta ${OUT_PATH}/${file}_sta.tcl -exit -no_splash &> ${OUT_PATH}/${file}_sta.out
done

cd "${SCRIPT_ROOT}"
