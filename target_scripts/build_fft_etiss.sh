#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

SCRIPT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INTEGRATOR_PATH="${SCRIPT_ROOT}"/..
FFT_PATH="${INTEGRATOR_PATH}/fft"
BUILD_PATH="${FFT_PATH}/build"

if [ -z "$RISCV_TOOLCHAIN_PATH_UNCHANGED" ]; then
  echo "Error: RISCV_TOOLCHAIN not set, please source .env!"
  exit 1
fi

LLVM_PATH="$1"
ARCH="$2" # rv32imafc_zcmp
CC="$LLVM_PATH/clang"
# --sysroot=${RISCV_TOOLCHAIN_PATH_UNCHANGED}/riscv32-unknown-elf --gcc-toolchain=${RISCV_TOOLCHAIN_PATH_UNCHANGED}/ -static -mllvm -global-isel=1 -mllvm -global-isel-abort=0 -Oz -march=${RISCV_ARCH} -mabi=${RISCV_ABI} -mno-save-restore -fno-builtin-bcmp
CFLAGS="-lc -lgcc -lsemihost -mllvm -global-isel=1 -mllvm -global-isel-abort=0 -D__riscv__ -Oz -march=$ARCH -mabi=ilp32 --sysroot=${RISCV_TOOLCHAIN_PATH_UNCHANGED}/riscv32-unknown-elf --gcc-toolchain=${RISCV_TOOLCHAIN_PATH_UNCHANGED}/ -static -I${BUILD_PATH}/support -DWARMUP_HEAT=1 -DGLOBAL_SCALE_FACTOR=1"

rm -rf ${BUILD_PATH}
mkdir -p ${BUILD_PATH}

cp ${INTEGRATOR_PATH}/res/CMakeLists.txt ${BUILD_PATH}
cp ${INTEGRATOR_PATH}/res/elffile.ini.in ${BUILD_PATH}
cp ${INTEGRATOR_PATH}/res/etiss.ld.in ${BUILD_PATH}
cp ${INTEGRATOR_PATH}/res/etiss.ld ${BUILD_PATH}
cp ${INTEGRATOR_PATH}/res/etiss-semihost.specs ${BUILD_PATH}
cp ${INTEGRATOR_PATH}/res/memsegs.ini.in ${BUILD_PATH}
cp ${INTEGRATOR_PATH}/res/rv32imacfd-toolchain.cmake ${BUILD_PATH}

cp -r ${INTEGRATOR_PATH}/res/fft.ini ${BUILD_PATH}
cp -r ${INTEGRATOR_PATH}/res/riscv_crt0/ ${BUILD_PATH}

# Build embench-iot for etiss
echo ""
echo "INFO: build benches"
cd ${BUILD_PATH}

${CC} -march=rv32im_zicsr_zifencei -mabi=ilp32 \
  ${FFT_PATH}/fft.c \
  -T ${BUILD_PATH}/etiss.ld  \
  -o ${BUILD_PATH}/fft -DCPU_MHZ=1 $CFLAGS

cd "${SCRIPT_ROOT}"
