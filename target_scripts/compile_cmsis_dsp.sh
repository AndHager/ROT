set -ue

SCRIPT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CMSIS_DIR="${SCRIPT_ROOT}/../cmsis-dsp-riscv"
BUILD_DIR="${CMSIS_DIR}/build-riscv"
LOG_DIR="${CMSIS_DIR}/log"

cd "$BUILD_DIR"

mkdir -p build && rm -rf build && mkdir build
cd build
cmake .. -DCMAKE_TOOLCHAIN_FILE=../riscv32-toolchain.cmake
make -j10

cd "$SCRIPT_ROOT"
