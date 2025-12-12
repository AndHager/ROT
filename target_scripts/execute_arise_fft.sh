#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

SCRIPT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
OUT_PATH="$1"
ETISS_ARCH=RV32IMACFD_XARISE

echo "  INFO Executing: ${SCRIPT_ROOT}/../etiss/etiss_arise/bin/bare_etiss_processor  --arch.cpu $ETISS_ARCH -p PrintInstruction -i${SCRIPT_ROOT}/../fft/build/fft.ini"
{
    timeout 60s ${SCRIPT_ROOT}/../etiss/etiss_arise/bin/bare_etiss_processor  --arch.cpu $ETISS_ARCH -p PrintInstruction -i${SCRIPT_ROOT}/../fft/build/fft.ini &> $OUT_PATH/fft_trace_etiss.txt
} || {
    echo "ERROR: timeout" >> $OUT_PATH/fft_trace_etiss.txt
    echo "    ${SCRIPT_ROOT}/../etiss/etiss_arise/bin/bare_etiss_processor --arch.cpu $ETISS_ARCH -p PrintInstruction -i${SCRIPT_ROOT}/../fft/build/fft.ini" >> $OUT_PATH/fft_trace_etiss.txt
}
