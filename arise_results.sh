#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

SCRIPT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
OUT_DIR="$1"
for method in static dynamic;
do
    echo ""
    echo "__${method}__"
    for target in size count;
    do
        echo ""
        echo "${target}__"
        for file in aha-mont64 crc32 depthconv edn huffbench matmult-int md5sum nettle-aes nettle-sha256 nsichneu picojpeg qrduino sglib-combined statemate tarfind ud wikisort xgboost;
        do
            echo "${file}:"
            base_file_name="ARISE32_${file}_${method}_${target}"
            cdsl="$base_file_name.core_desc"
            if [ -f "$OUT_DIR/$cdsl" ]; then
                out_method="$base_file_name"

                fn=""
                if [ "$method" = "static" ] ; then
                    fn="${file}.etiss_asm"
                else 
                    fn="${file}_trace_etiss.txt"
                fi


                python3 $SCRIPT_ROOT/analysis/eval.py --path $OUT_DIR "--$method" True "--$target" True $fn $out_method/$fn
            fi
        done
    done
done
