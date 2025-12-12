#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

SCRIPT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

ETISS_DIR=$SCRIPT_ROOT/etiss
ETISS_ARCH="RV32IMACFD_XARISE"

export PYTHONPATH=$SCRIPT_ROOT/M2-ISA-R/

source M2-ISA-R/venv/bin/activate

python -m m2isar.frontends.coredsl2.parser cdsl/top.core_desc
python -m m2isar.backends.etiss.writer cdsl/gen_model/top.m2isarmodel --separate --static-scalars

deactivate

cp -r cdsl/gen_output/top/$ETISS_ARCH $ETISS_DIR/ArchImpl/

cd $ETISS_DIR
cp ArchImpl/RV32IMACFD/RV32IMACFDArchSpecificImp.cpp ArchImpl/$ETISS_ARCH/${ETISS_ARCH}ArchSpecificImp.cpp
sed -i "s/RV32IMACFD/$ETISS_ARCH/g" ArchImpl/$ETISS_ARCH/${ETISS_ARCH}ArchSpecificImp.cpp

cd $SCRIPT_ROOT
