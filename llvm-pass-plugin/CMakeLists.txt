cmake_minimum_required(VERSION 3.8)


if(NOT DEFINED ENV{RISCV_TOOLCHAIN_PATH_CHANGED})
  message(FATAL_ERROR "Environment variable 'RISCV_TOOLCHAIN_PATH_CHANGED' is not set. Please source .env before running cmake.")
endif()
set(RISCV_TOOLCHAIN_PATH_CHANGED $ENV{RISCV_TOOLCHAIN_PATH_CHANGED})

project("CDFG Analyzer" VERSION 1.0.0)

# TODO: Is that still correct, it was /usr/riscv/ before
find_package(LLVM 18.1.3 EXACT  REQUIRED CONFIG PATHS ${RISCV_TOOLCHAIN_PATH_CHANGED}/lib)

message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")
message(STATUS "Using LLVMConfig.cmake in: ${LLVM_DIR}")

add_definitions(${LLVM_DEFINITIONS})
include_directories(${LLVM_INCLUDE_DIRS})
link_directories(${LLVM_LIBRARY_DIRS})

add_library(LLVMCDFG MODULE
    src/pass.cpp
)

TARGET_LINK_LIBRARIES(LLVMCDFG libmgclient.so.2)

SET(CMAKE_CXX_FLAGS "-Wall -Werror")
