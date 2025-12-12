#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

SCRIPT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

ETISS_DIR=$SCRIPT_ROOT/etiss
INSTALL_DIR=$ETISS_DIR/etiss_arise


cd $ETISS_DIR
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$INSTALL_DIR
cmake --build build -j`nproc`
cmake --install build
cd $SCRIPT_ROOT
