set -ue

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_PATH="$1"

cp ${SCRIPT_ROOT}/../cmsis-dsp-riscv/build-riscv/build/example ${OUT_PATH}/cmsis-example

cd ${OUT_PATH}

llvm-objdump -r -M no-aliases -d cmsis-example 1>${OUT_PATH}/cmsis-example.asm

cd ${SCRIPT_ROOT}
