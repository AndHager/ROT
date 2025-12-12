#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

SCRIPT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
OUT_PATH="$1"
ETISS_ARCH=RV32IMACFD

for file in aha-mont64 crc32 cubic edn huffbench matmult-int md5sum minver nbody nettle-aes nettle-sha256 nsichneu picojpeg primecount qrduino sglib-combined slre st statemate tarfind ud wikisort;
do 
    echo "  INFO Executing: ${SCRIPT_ROOT}/../etiss/etiss_arise/bin/bare_etiss_processor -pluginToLoad PrintInstruction -i${SCRIPT_ROOT}/../embench-iot/bd/install/ini/${file}.ini"
    {
        # $OUT_PATH/${file}_trace_etiss.txt
        timeout 60s ${SCRIPT_ROOT}/../etiss/etiss_arise/bin/bare_etiss_processor -p PrintInstruction -i${SCRIPT_ROOT}/../embench-iot/bd/install/ini/${file}.ini --arch.cpu=$ETISS_ARCH &> $OUT_PATH/${file}_trace_etiss.txt
    } || {
        echo "ERROR: timeout" >> $OUT_PATH/${file}_trace_etiss.txt
        echo "    timeout 60s ${SCRIPT_ROOT}/../etiss/etiss_arise/bin/bare_etiss_processor -p PrintInstruction -i${SCRIPT_ROOT}/../embench-iot/bd/install/ini/${file}.ini --arch.cpu=$ETISS_ARCH" >> $OUT_PATH/${file}_trace_etiss.txt
    }
done
