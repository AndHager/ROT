#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

if [ -z "$RISCV_TOOLCHAIN_PATH_UNCHANGED" ]; then
  echo "Error: RISCV_TOOLCHAIN not set, please source .env!"
  exit 1
fi

SCRIPT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INTEGRATOR_PATH="${SCRIPT_ROOT}"/..
EMBENCH_PATH="${INTEGRATOR_PATH}/embench-iot"
BUILD_PATH="${EMBENCH_PATH}/bd/build"
SUPPORT_PATH="${EMBENCH_PATH}/support"
BD_SUPPORT_PATH="${EMBENCH_PATH}/bd/support"

LLVM_PATH="$1"
ARCH="$2" # rv32imacfd_zcmp

CC_BASE="${RISCV_TOOLCHAIN_PATH_UNCHANGED}/bin/clang"
CC="$LLVM_PATH/clang"
# -fuse-ld=lld --sysroot=${RISCV_TOOLCHAIN_PATH_UNCHANGED}/riscv32-unknown-elf --gcc-toolchain=${RISCV_TOOLCHAIN_PATH_UNCHANGED}/ -static -mllvm -global-isel=1 -mllvm -global-isel-abort=0 -Oz -march=${RISCV_ARCH} -mabi=${RISCV_ABI} -mno-save-restore -fno-builtin-bcmp
CFLAGS="-fuse-ld=lld -mllvm -global-isel=1 -mllvm -global-isel-abort=0 --sysroot=${RISCV_TOOLCHAIN_PATH_UNCHANGED}/riscv32-unknown-elf --gcc-toolchain=${RISCV_TOOLCHAIN_PATH_UNCHANGED}/ -D__riscv__ -Oz -march=$ARCH -mabi=ilp32 -static -fno-builtin-bcmp -I${SUPPORT_PATH} -I${EMBENCH_PATH}/config/riscv32/boards/ri5cyverilator -I${EMBENCH_PATH}/config/riscv32/chips/generic -I${EMBENCH_PATH}/config/riscv32 -DCPU_MHZ=1 -DWARMUP_HEAT=1"

if [[ "${1:-NONE}" == "clean" ]]; then
    rm -rf ${BUILD_PATH}
    rm -rf "${EMBENCH_PATH}/bd/install"
    exit
fi

# create build dir
cp -r ${INTEGRATOR_PATH}/res/* ${INTEGRATOR_PATH}/embench-iot/bd
cp -r ${EMBENCH_PATH}/src/* ${EMBENCH_PATH}/bd/src
cp -r ${EMBENCH_PATH}/support/* ${EMBENCH_PATH}/bd/support
cp -r ${EMBENCH_PATH}/config/* ${EMBENCH_PATH}/bd/config
mkdir -p ${BUILD_PATH}

# Build support Files for etiss
${CC} ${CFLAGS} -o ${BD_SUPPORT_PATH}/beebsc_etiss.o -c ${SUPPORT_PATH}/beebsc.c
${CC} ${CFLAGS} -o ${BD_SUPPORT_PATH}/main_etiss.o -c ${SUPPORT_PATH}/main.c
${CC} ${CFLAGS} -o ${BD_SUPPORT_PATH}/dummy-crt0_etiss.o -c ${SUPPORT_PATH}/dummy-crt0.c
${CC} ${CFLAGS} -o ${BD_SUPPORT_PATH}/dummy-libc_etiss.o -c ${SUPPORT_PATH}/dummy-libc.c
${CC} ${CFLAGS} -o ${BD_SUPPORT_PATH}/dummy-libgcc_etiss.o -c ${SUPPORT_PATH}/dummy-libgcc.c
${CC} ${CFLAGS} -o ${BD_SUPPORT_PATH}/dummy-libm_etiss.o -c ${SUPPORT_PATH}/dummy-libm.c

${CC} ${CFLAGS} -o ${EMBENCH_PATH}/bd/config/riscv32/chips/generic/chipsupport_etiss.o -c ${EMBENCH_PATH}/config/riscv32/chips/generic/chipsupport.c
${CC} ${CFLAGS} -o ${EMBENCH_PATH}/bd/config/riscv32/boards/ri5cyverilator/boardsupport_etiss.o -c ${EMBENCH_PATH}/config/riscv32/boards/ri5cyverilator/boardsupport.c

# Build embench-iot for etiss
cd ${BUILD_PATH}
cmake -DRISCV_ARCH=$ARCH -DCMAKE_BUILD_TYPE=Release -DCMAKE_TOOLCHAIN_FILE=rv32imacfd-toolchain.cmake -DRISCV_TOOLCHAIN_PREFIX=$LLVM_PATH -DCMAKE_INSTALL_PREFIX=../install/ ..
make -j8
make install

cd "${SCRIPT_ROOT}"
