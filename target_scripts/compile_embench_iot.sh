#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EMBENCH_DIR="${SCRIPT_ROOT}/../embench-iot"

OUT_PATH="$1"
LLVM_PATH="$2"

RISCV_ARCH="$3" # "rv32imacfd_xarise"
RISCV_ABI="ilp32"

cd "$EMBENCH_DIR"

# Build benchmarks
# -mllvm -print-after=riscv-make-compressible
# -mllvm -debug-pass=Structure -mllvm -print-after=riscv-replace-48
# -mllvm -global-isel=1 -mllvm -global-isel-abort=0
MUSL=${SCRIPT_ROOT}/../manual-vectorization-setup/musl-install

# base dummy libs: libm
# MUSL LDFLAGS:  $MUSL/lib/crt1.o $MUSL/lib/libc.a $MUSL/lib/libm.a  -nostartfiles //  -mabi=${RISCV_ABI} $MUSL/lib/crt1.o $MUSL/lib/libc.a -static  -nostartfiles
# -mllvm -global-isel=1 -mllvm -global-isel-abort=0  --sysroot=${RISCV_TOOLCHAIN_PATH_CHANGED}/riscv32-unknown-elf --gcc-toolchain=${RISCV_TOOLCHAIN_PATH_CHANGED}/
# -mno-save-restore -fno-builtin-bcmp
#  -nostartfiles -nostdlib
# $MUSL/lib/crt1.o $MUSL/lib/libc.a
python3 ./build_all.py \
  --clean \
  --verbose \
  --arch=riscv32 \
  --chip=generic \
  --board=ri5cyverilator \
  --cc="${LLVM_PATH}"/clang \
  --ld="${LLVM_PATH}"/clang \
  --cflags="-static -Oz -march=${RISCV_ARCH} -mabi=${RISCV_ABI} " \
  --ldflags="-static -march=${RISCV_ARCH} -mabi=${RISCV_ABI}" \
  --dummy-libs="libgcc libm"

cd "$SCRIPT_ROOT"

for file in aha-mont64 crc32 cubic edn huffbench matmult-int md5sum minver nbody nettle-aes nettle-sha256 nsichneu picojpeg primecount qrduino sglib-combined slre st statemate tarfind ud wikisort;
do
    echo "cp $EMBENCH_DIR/bd/src/${file}/${file} $OUT_PATH"
    cp $EMBENCH_DIR/bd/src/${file}/${file} $OUT_PATH
done
