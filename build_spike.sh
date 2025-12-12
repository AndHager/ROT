#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

if [ -z "$RISCV_TOOLCHAIN_PATH_UNCHANGED" ] || [ -z "$RISCV_TOOLCHAIN_PATH_CHANGED" ]; then
  echo "Error: RISCV_TOOLCHAIN not set, please source .env!"
  exit 1
fi

cd riscv-isa-sim
mkdir -p build
cd build
../configure --prefix=${RISCV_TOOLCHAIN_PATH_CHANGED} --with-isa=rv32imac_zifencei
make -j12
cd ..


cd riscv-pk
mkdir -p build
cd build
CC=${RISCV_TOOLCHAIN_PATH_CHANGED}/bin/riscv32-unknown-elf-gcc CXX=${RISCV_TOOLCHAIN_PATH_CHANGED}/bin/riscv32-unknown-elf-g++ OBJCOPY=${RISCV_TOOLCHAIN_PATH_CHANGED}/bin/riscv32-unknown-elf-objcopy ../configure --bindir=${RISCV_TOOLCHAIN_PATH_UNCHANGED} --host=riscv32-unknown-elf --with-arch=rv32imac_zifencei --with-abi=ilp32 --prefix=${RISCV_TOOLCHAIN_PATH_UNCHANGED}
make -j8
cd ../../..
