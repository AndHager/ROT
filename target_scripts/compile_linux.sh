#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

SCRIPT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
OUt_DIR="$1"
TOOL_DIR="$2"
LINUX_DIR="${SCRIPT_ROOT}/../../linux-6.8.9"
CONF_DIR="${LINUX_DIR}/arch/riscv/configs"


cd $LINUX_DIR
cat $CONF_DIR/32-bit.config $CONF_DIR/defconfig > $CONF_DIR/32_defconfig

# Build with clang
make mrproper
make -j12 ARCH=riscv CROSS_COMPILE=$TOOL_DIR/riscv32-unknown-linux-gnu- LLVM=1 CC=$TOOL_DIR/clang O=./build 32_defconfig
cd build
make -j12 ARCH=riscv CROSS_COMPILE=$TOOL_DIR/riscv32-unknown-linux-gnu- LLVM=1 CC=$TOOL_DIR/clang

cd $LINUX_DIR
mv build build_clang

# Build with gcc
# make mrproper
# make -j12 ARCH=riscv CROSS_COMPILE=$TOOL_DIR/riscv32-unknown-linux-gnu- O=./build 32_defconfig
# cd build
# make -j12 ARCH=riscv CROSS_COMPILE=$TOOL_DIR/riscv32-unknown-linux-gnu-

# cd $LINUX_DIR
# mv build build_gcc

cd "$SCRIPT_ROOT"
