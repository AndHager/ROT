#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

SCRIPT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
OUT_PATH="$1"
FILE="$2"
ETISS_ARCH=RV32IMACFD_XARISE

for file in $FILE;
do 
    echo "  INFO Executing: ${SCRIPT_ROOT}/../etiss/etiss_arise/bin/bare_etiss_processor -pluginToLoad PrintInstruction -i${SCRIPT_ROOT}/../embench-iot/bd/install/ini/${file}.ini"
    {
        timeout 60s ${SCRIPT_ROOT}/../etiss/etiss_arise/bin/bare_etiss_processor -p PrintInstruction -i${SCRIPT_ROOT}/../embench-iot/bd/install/ini/${file}.ini --arch.cpu=$ETISS_ARCH &> $OUT_PATH/${file}_trace_etiss.txt
    } || {
        echo "ERROR: timeout" >> $OUT_PATH/${file}_trace_etiss.txt
        echo "    timeout 60s ${SCRIPT_ROOT}/../etiss/etiss_arise/bin/bare_etiss_processor -p PrintInstruction -i${SCRIPT_ROOT}/../embench-iot/bd/install/ini/${file}.ini --arch.cpu=$ETISS_ARCH" >> $OUT_PATH/${file}_trace_etiss.txt
    }
done
