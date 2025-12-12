#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

SCRIPT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
OUT_DIR="$1"

cd "${OUT_DIR}"
# etiss_
ASM=$(printf  '%s ' *.asm)
echo $ASM
cd "${SCRIPT_ROOT}"

echo ""
echo "#################"
echo "## Static Size ##"
echo "#################"
(
    set -x 
    python3 ${SCRIPT_ROOT}/analysis/generator.py --static True --size True --results False --path ${OUT_DIR} ${ASM}
)
# echo ""
# echo "##################"
# echo "## Static Count ##"
# echo "##################"
# python3 ${SCRIPT_ROOT}/analysis/generator.py --static True --count True --path ${OUT_DIR} ${ASM}

echo ""
echo "##################"
echo "## Dynamic Size ##"
echo "##################"
(
    set -x 
    python3 ${SCRIPT_ROOT}/analysis/generator.py --dynamic True --size True --results False --path ${OUT_DIR} ${ASM}
)

echo ""
echo "###################"
echo "## Dynamic Count ##"
echo "###################"
(
    set -x 
    python3 ${SCRIPT_ROOT}/analysis/generator.py --dynamic True --count True --results False --path ${OUT_DIR} ${ASM}
)
