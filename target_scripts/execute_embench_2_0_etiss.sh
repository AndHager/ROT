#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

SCRIPT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
OUT_PATH="$1"
ETISS_ARCH=RV32IMACFD

for file in aha-mont64 crc32 depthconv edn huffbench matmult-int md5sum nettle-aes nettle-sha256 nsichneu picojpeg qrduino sglib-combined statemate tarfind ud wikisort xgboost;
do 
    echo "  INFO Executing: ${SCRIPT_ROOT}/../etiss/etiss_arise/bin/bare_etiss_processor -p PrintInstruction -i${SCRIPT_ROOT}/../embench-iot-2/bd/install/ini/${file}.ini --arch.cpu=$ETISS_ARCH"
    {
        # $OUT_PATH/${file}_trace_etiss.txt
        timeout 60s ${SCRIPT_ROOT}/../etiss/etiss_arise/bin/bare_etiss_processor -p PrintInstruction -i${SCRIPT_ROOT}/../embench-iot-2/bd/install/ini/${file}.ini --arch.cpu=$ETISS_ARCH &> $OUT_PATH/${file}_trace_etiss.txt
    } || {
        echo "ERROR: timeout" >> $OUT_PATH/${file}_trace_etiss.txt
        echo "    ${SCRIPT_ROOT}/../etiss/etiss_arise/bin/bare_etiss_processor -p PrintInstruction -i${SCRIPT_ROOT}/../embench-iot-2/bd/install/ini/${file}.ini --arch.cpu=$ETISS_ARCH" >> $OUT_PATH/${file}_trace_etiss.txt
    }
done
