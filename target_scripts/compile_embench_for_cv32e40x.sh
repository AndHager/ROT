#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EMBENCH_DIR="${SCRIPT_ROOT}/../embench-iot"

LLVM_PATH="$1"

RISCV_ARCH="$2" # "rv32imafdc_xarise"
RISCV_ABI="ilp32"

cd "$EMBENCH_DIR"

# Build
# ${RISCV_TOOLCHAIN_PATH_UNCHANGED}/bin/clang -static -Oz -march=rv32imafc -mabi=ilp32 -mno-save-restore -fno-builtin-bcmp -I/home/<USER>/Desktop/CodeComp/integrator/embench-iot/support -I/home/<USER>/Desktop/CodeComp/integrator/embench-iot/config/riscv32/boards/ri5cyverilator -I/home/<USER>/Desktop/CodeComp/integrator/embench-iot/config/riscv32/chips/generic -I/home/<USER>/Desktop/CodeComp/integrator/embench-iot/config/riscv32 -DCPU_MHZ=1 -DWARMUP_HEAT=1 -o mont64.o -c /home/<USER>/Desktop/CodeComp/integrator/embench-iot/src/aha-mont64/mont64.c

# Link
# ${RISCV_TOOLCHAIN_PATH_UNCHANGED}/bin/clang -lgcc -lc -static -march=rv32imafc -mabi=ilp32 -nostartfiles -Wl,-T,link.ld,--print-memory-usage -o aha-mont64 mont64.o /home/<USER>/Desktop/CodeComp/integrator/embench-iot/bd/config/riscv32/chips/generic/chipsupport.o /home/<USER>/Desktop/CodeComp/integrator/embench-iot/bd/config/riscv32/boards/ri5cyverilator/boardsupport.o /home/<USER>/Desktop/CodeComp/integrator/embench-iot/bd/support/main.o /home/<USER>/Desktop/CodeComp/integrator/embench-iot/bd/support/beebsc.o /home/<USER>/Desktop/CodeComp/integrator/embench-iot/bd/support/dummy-libm.o

# Mem file
# ${RISCV_TOOLCHAIN_PATH_UNCHANGED}/bin/riscv32-unknown-elf-objcopy -O verilog aha-mont64 aha-mont64.mem

# -mllvm -debug-pass=Structure -mllvm -print-after=riscv-replace-48

MUSL=${SCRIPT_ROOT}/../manual-vectorization-setup/musl-install

# Build benchmarks
# -mllvm -print-after=riscv-make-compressible

# base dummy libs:  libm
# -mllvm -align-all-functions=2 -mllvm -align-all-blocks=2 
# musl LDFLAGS: -static $MUSL/lib/crt1.o $MUSL/lib/libc.a $MUSL/lib/libm.a  -nostartfiles
# -mno-save-restore -fno-builtin-bcmp
python3 ./build_all.py \
  --clean \
  --verbose \
  --arch=riscv32 \
  --chip=generic \
  --board=ri5cyverilator \
  --cc=$LLVM_PATH/clang \
  --ld=$LLVM_PATH/clang \
  --cflags="-static -Oz -march=${RISCV_ARCH} -mabi=${RISCV_ABI} " \
  --ldflags="-static -lgcc -lc -march=${RISCV_ARCH} -mabi=${RISCV_ABI} -Wl,-T,$SCRIPT_ROOT/../firmware/link.ld,--print-memory-usage" \
  --dummy-libs="libgcc libm"


for file in $(ls $EMBENCH_DIR/src); do
  (
    set -x
    $LLVM_PATH/riscv32-unknown-elf-objcopy -O verilog $EMBENCH_DIR/bd/src/${file}/${file} $EMBENCH_DIR/bd/src/${file}/firmware.mem
  )
done

cd "$SCRIPT_ROOT"
