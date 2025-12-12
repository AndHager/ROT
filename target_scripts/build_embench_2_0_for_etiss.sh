#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

SCRIPT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INTEGRATOR_PATH="${SCRIPT_ROOT}"/..
EMBENCH_PATH="${INTEGRATOR_PATH}/embench-iot-2"
BUILD_PATH="${EMBENCH_PATH}/bd"

LLVM_PATH="$1"
ARCH="$2" # rv32imafc_zcmp

if [ -z "$RISCV_TOOLCHAIN_PATH_UNCHANGED" ]; then
  echo "Error: RISCV_TOOLCHAIN not set, please source .env!"
  exit 1
fi

RISCV_TOOLCHAIN_PATH_CHANGED="$RISCV_TOOLCHAIN_PATH_UNCHANGED"
RISCV_TOOLCHAIN_PREFIX="$RISCV_TOOLCHAIN_PATH_UNCHANGED"
CC="$LLVM_PATH/clang"
# --sysroot=${RISCV_TOOLCHAIN_PATH_UNCHANGED}/riscv32-unknown-elf --gcc-toolchain=${RISCV_TOOLCHAIN_PATH_UNCHANGED}/ -static -mllvm -global-isel=1 -mllvm -global-isel-abort=0 -Oz -march=${RISCV_ARCH} -mabi=${RISCV_ABI} -mno-save-restore -fno-builtin-bcmp
CFLAGS="-lc -lgcc -lsemihost -mllvm -global-isel=1 -mllvm -global-isel-abort=0 -D__riscv__ -Oz -march=$ARCH -mabi=ilp32 --sysroot=${RISCV_TOOLCHAIN_PATH_UNCHANGED}/riscv32-unknown-elf --gcc-toolchain=${RISCV_TOOLCHAIN_PATH_UNCHANGED}/ -static -I${BUILD_PATH}/support -DWARMUP_HEAT=1 -DGLOBAL_SCALE_FACTOR=1"

rm -rf ${BUILD_PATH}
mkdir -p ${BUILD_PATH}
mkdir -p ${BUILD_PATH}/install
mkdir -p ${BUILD_PATH}/install/bin
mkdir -p ${BUILD_PATH}/install/ini
mkdir -p ${BUILD_PATH}/src
mkdir -p ${BUILD_PATH}/support
mkdir -p ${BUILD_PATH}/config

# create build dir
cp ${INTEGRATOR_PATH}/res/CMakeLists.txt ${BUILD_PATH}
cp ${INTEGRATOR_PATH}/res/elffile.ini.in ${BUILD_PATH}
cp ${INTEGRATOR_PATH}/res/etiss.ld.in ${BUILD_PATH}
cp ${INTEGRATOR_PATH}/res/etiss.ld ${BUILD_PATH}
cp ${INTEGRATOR_PATH}/res/etiss-semihost.specs ${BUILD_PATH}
cp ${INTEGRATOR_PATH}/res/memsegs.ini.in ${BUILD_PATH}
cp ${INTEGRATOR_PATH}/res/rv32imacfd-toolchain.cmake ${BUILD_PATH}

cp -r ${INTEGRATOR_PATH}/res/ini/ ${BUILD_PATH}/install
cp -r ${INTEGRATOR_PATH}/res/riscv_crt0/ ${BUILD_PATH}
cp -r ${INTEGRATOR_PATH}/res/src_embench_2_0 ${BUILD_PATH}
cp -r ${BUILD_PATH}/src_embench_2_0/* ${BUILD_PATH}/src
rm -r ${BUILD_PATH}/src_embench_2_0/

cp -r ${EMBENCH_PATH}/src/* ${BUILD_PATH}/src
cp -r ${EMBENCH_PATH}/support/* ${BUILD_PATH}/support
cp -r ${EMBENCH_PATH}/examples/native/size/* ${BUILD_PATH}/support

# Build support Files for etiss
# -c -fdata-sections -ffunction-sections -Oz -march=rv32imafc -mabi=ilp32 -DWARMUP_HEAT=1 -DGLOBAL_SCALE_FACTOR=1 -Isupport 

echo "INFO: build support files"
echo "${CC} ${CFLAGS} -o ${BUILD_PATH}/support/main_etiss.o -c ${BUILD_PATH}/support/main.c"
${CC} ${CFLAGS} -o ${BUILD_PATH}/support/main_etiss.o -c ${BUILD_PATH}/support/main.c

echo "${CC} ${CFLAGS} -o ${BUILD_PATH}/support/beebsc_etiss.o -c ${BUILD_PATH}/support/beebsc.c"
${CC} ${CFLAGS} -o ${BUILD_PATH}/support/beebsc_etiss.o -c ${BUILD_PATH}/support/beebsc.c

echo "${CC} ${CFLAGS} -o ${BUILD_PATH}/support/boardsupport_etiss.o -c  ${BUILD_PATH}/support/boardsupport.c"
${CC} ${CFLAGS} -o ${BUILD_PATH}/support/boardsupport_etiss.o -c  ${BUILD_PATH}/support/boardsupport.c

# Build embench-iot for etiss
echo ""
echo "INFO: build benches"
cd ${BUILD_PATH}

for file in aha-mont64 crc32 depthconv edn huffbench matmult-int md5sum nettle-aes nettle-sha256 nsichneu picojpeg qrduino sglib-combined statemate tarfind ud wikisort xgboost; do
  (
    set -x
    ${CC} -march=rv32im_zicsr_zifencei -mabi=ilp32 \
      ${BUILD_PATH}/support/main.c ${BUILD_PATH}/src/$file/*.c ${BUILD_PATH}/support/beebsc.c ${BUILD_PATH}/support/boardsupport.c ${BUILD_PATH}/riscv_crt0/crt0.S ${BUILD_PATH}/riscv_crt0/trap_handler.c \
      -T ${BUILD_PATH}/etiss.ld -nostdlib \
      -o ${BUILD_PATH}/install/bin/$file -I./support -DCPU_MHZ=1 $CFLAGS
  )
done

# echo "RISCV_TOOLCHAIN_PREFIX=$LLVM_PATH cmake -DCMAKE_C_COMPILER=${CC} -DRISCV_ARCH=$ARCH -DCMAKE_BUILD_TYPE=Release -DCMAKE_TOOLCHAIN_FILE=${BUILD_PATH}/rv32imacfd-toolchain.cmake  -DCMAKE_RULE_MESSAGES:BOOL=OFF -DCMAKE_VERBOSE_MAKEFILE:BOOL=ON  -DRISCV_TOOLCHAIN_PREFIX=$LLVM_PATH -DCMAKE_INSTALL_PREFIX=./install/ ."
# RISCV_TOOLCHAIN_PATH_UNCHANGED=$RISCV_TOOLCHAIN_PATH_UNCHANGED cmake -DCMAKE_C_COMPILER=${CC} -DRISCV_ARCH=$ARCH -DCMAKE_BUILD_TYPE=Release -DCMAKE_TOOLCHAIN_FILE=${BUILD_PATH}/rv32imacfd-toolchain.cmake -DRISCV_TOOLCHAIN_PREFIX=$RISCV_TOOLCHAIN_PREFIX -DCMAKE_INSTALL_PREFIX=./install/ .
# make -j8  --no-print-directory
# make install  --no-print-directory

cd "${SCRIPT_ROOT}"
