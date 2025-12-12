#!/bin/bash
# Author: Andreas Hager-Clukas
# Email: andreas.hager-clukas@hm.edu
set -ue

echo " ____  _          _ _              "
echo "/ ___|(_)______ _| (_)_______ _ __ "
echo "\___ \| |_  / _\` | | |_  / _ \ '__|"
echo " ___) | |/ / (_| | | |/ /  __/ |   "
echo "|____/|_/___\__,_|_|_/___\___|_|   "



if [ -z "$RISCV_TOOLCHAIN_PATH" ]; then
  echo "Error: RISCV_TOOLCHAIN_PATH not set, please source .env or execute: `RISCV_TOOLCHAIN_PATH=<PATH> ./bax.sh ...`!"
  exit 1
fi

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_TARGET=${SCRIPT_ROOT}/target_scripts
SCRIPT_ANALYSIS=${SCRIPT_ROOT}/analysis
OUT_DIR=${SCRIPT_ROOT}/out
DEFAULT_LLVM="${RISCV_TOOLCHAIN_PATH}/bin/"
DEFAULT_RISCV_ARCH="rv32gc_xarise"

# Set default values
clean=false

musl=false
embench=false
embench_2=false
linux=false
cmsis=false
fft=false

out=$OUT_DIR
llvm=$DEFAULT_LLVM
arch=$DEFAULT_RISCV_ARCH

start_db=false
purge_db=false
build_cpu=false
build_dfg=false
analyze_dfg=false
build_target=false
analyze_binary=false
run_embench_size=false
run_target=false
use_etiss=false
use_spike=false
run_cpu=false
entropy=false
analyze_traces=false

generate_insts=false

debug=false


# Usage manual entry
usage() {
  cat <<EOF
Usage: ${0##*/} [OPTIONS]

This script builds and executes the Analysis for Embench-iot.

Available options:

    --clean               Clean run full analysis (default: $clean)

    --musl                Set target to musl (default: $musl)
    --embench             Set target to Embench-IoT 1.0 (default: $embench)
    --embench-2           Set target to Embench-IoT 2.0  (default: $embench_2)
    --cmsis               Set target to CMSIS (default: $cmsis)
    --linux               Set target to Linux (default: $linux)
    --fft                 Set target to FFT (default: $linux)

    --out                 Set out dir (default: $out)
    --llvm                Set llvm path (default: $llvm)
    --arch                Set arch (default: $arch)

    --start-db            Start the database service (default: $start_db)
    --purge-db            Purge the database (default: $purge_db)
    --build-cpu           Build the cv32e40x core (default: $build_cpu)
    --build-dfg           Build the data flow graph (default: $build_dfg)
    --analyze-dfg         Analyze the data flow graph (default: $analyze_dfg)
    --build-target        Build target (default: $build_target)
    --analyze-binary      Analyze binary files (default: $analyze_binary)
    --run-embench-size    Run Embench benchmark for size (default: $run_embench_size)
    --run-target          Run target in simulator (spike/ETISS) (default: $run_target)
    --use-etiss           Run target in ETISS (default: $use_etiss) 
    --use-spike           Run target in spike (default: $use_spike) 
    --run-cpu             Run target in cv32e40x core (default: $run_cpu)
    --entropy             Entropy analysis (default: $entropy)
    --analyze-traces      Enable trace analysis (default: $analyze_traces)
    --generate-insts      Enable instruction generation (default: $generate_insts)
    --help                Display this help and exit

EOF
  exit
}

# Loop through arguments and process them
while [[ $# -gt 0 ]]; do
  case $1 in
  --clean)
    clean=true
    shift # Remove --clean from processing
    ;;
  --start-db)
    start_db=true
    shift # Remove --start-db from processing
    ;;
  --build-cpu)
    build_cpu=true
    shift # Remove --build-cpu from processing
    ;;
  --embench)
    embench=true
    shift # Remove --embench from processing
    ;;
  --embench-2)
    embench_2=true
    shift # Remove --embench-2 from processing
    ;;
  --fft)
    fft=true
    shift # Remove --fft from processing
    ;;
  --musl)
    musl=true
    shift # Remove --musl from processing
    ;;
  --cmsis)
    cmsis=true
    shift # Remove --cmsis from processing
    ;;
  --out)
    out="$2"
    shift # Remove --out from processing
    shift # Remove value from processing
    ;;
  --llvm)
    llvm="$2"
    shift # Remove --llvm from processing
    shift # Remove value from processing
    ;;
  --arch)
    arch="$2"
    shift # Remove --arch from processing
    shift # Remove value from processing
    ;;
  --linux)
    linux=true
    shift # Remove --linux from processing
    ;;
  --purge-db)
    purge_db=true
    shift # Remove --purge-db from processing
    ;;
  --build-dfg)
    build_dfg=true
    shift # Remove --build-dfg from processing
    ;;
  --analyze-dfg)
    analyze_dfg=true
    shift # Remove --analyze-dfg from processing
    ;;
  --build-target)
    build_target=true
    shift # Remove --build-target from processing
    ;;
  --analyze-binary)
    analyze_binary=true
    shift # Remove --analyze-binary from processing
    ;;
  --entropy)
    entropy=true
    shift # Remove --entropy from processing
    ;;
  --run-embench-size)
    run_embench_size=true
    shift # Remove --run-embench-size from processing
    ;;
  --run-target)
    run_target=true
    shift # Remove --run-target from processing
    ;;
  --use-etiss)
    use_etiss=true
    shift # Remove --use-etiss from processing
    ;;
  --use-spike)
    use_spike=true
    shift # Remove --use-spike from processing
    ;;
  --run-cpu)
    run_cpu=true # Remove --run-cpu from processing
    shift
    ;;
  --analyze-traces)
    analyze_traces=true
    shift # Remove --analyze-traces from processing
    ;;
  --generate-insts)
    generate_insts=true
    shift # Remove --generate-insts from processing
    ;;
  --help)
    usage
    ;;
  *)
    # Unknown option
    echo "Error: Invalid option $1"
    exit 1
    ;;
  esac
done

set -- "${POSITIONAL_ARGS[@]}" # restore positional parameters

if [ "$clean" = true ]; then
  start_db=true
  purge_db=true
  build_cpu=true
  build_llvm=true
  build_dfg=true
  analyze_dfg=true
  build_target=true
  analyze_binary=true

  run_embench_size=true
  run_embench=true

  analyze_traces=true
fi

if [ "$debug" = true ]; then
  echo "INFO params:"
  echo "  clean=$clean"
  echo "  start_db=$start_db"
  echo "  purge_db=$purge_db"
  echo "  build_llvm=$build_llvm"
  echo "  build_dfg=$build_dfg"
  echo "  analyze_dfg=$analyze_dfg"
  echo "  build_target=$build_target"
  echo "  analyze_binary=$analyze_binary"

  if [ "$embench" = true ]; then
    echo "  run_embench_size=$run_embench_size"
    echo "  run_embench=$run_embench"
  fi

  echo "  analyze_traces=$analyze_traces"
fi

out="$(
  cd "$(dirname "$out")"
  pwd
)/$(basename "$out")"

if [ "$clean" = true ]; then
  echo "INFO: Cleaning old $out"
  rm -r ${out} || true
fi

mkdir -p ${out}

if [ "$purge_db" = true ]; then
  echo "INFO: Start memgraph"
  docker start memgraph &>${out}/docker_start_out.txt
fi

if [ "$purge_db" = true ]; then
  echo "INFO: Purge db"
  echo "MATCH (N) DETACH DELETE N;" | mgconsole
fi

if [ "$build_cpu" = true ]; then
  echo "INFO: build cpu"
  ${SCRIPT_ROOT}/build_cpu.sh &>${out}/build_cpu_log.txt
fi

if [ "$build_dfg" = true ]; then
  # build dfg pass
  echo "INFO: Build DFG analysis LLVM-Pass"
  ${SCRIPT_ROOT}/build_dfg_pass.sh &>${out}/dfg_pass_build.txt

  # Static analyze benchmark
  echo "INFO: Building DFG"
  if [ "$embench" = true ]; then
    ${SCRIPT_TARGET}/static_dfg_analyze_embench_iot.sh &>${out}/embench_dfg_pass_run.txt
  fi

  if [ "$embench_2" = true ]; then
    ${SCRIPT_TARGET}/static_dfg_analyze_embench_2_0_iot.sh &>${out}/embench_dfg_pass_run.txt
  fi

  if [ "$cmsis" = true ]; then
    ${SCRIPT_TARGET}/static_dfg_analyze_cmsis_dsp.sh &>${out}/cmsis_dfg_pass_run.txt
  fi

  if [ "$musl" = true ]; then
    ${SCRIPT_TARGET}/static_dfg_analyze_musl.sh &>${out}/musl_dfg_pass_run.txt
  fi

  if [ "$linux" = true ]; then
    ${SCRIPT_TARGET}/static_dfg_analyze_linux.sh $llvm &>${out}/linux_dfg_pass_run.txt
  fi
fi

if [ "$analyze_dfg" = true ]; then
  echo "INFO: Analyzing DFG"
  python3 ${SCRIPT_ANALYSIS}/dfg.py --pdc True &>${out}/dfg_analysis.txt
fi

if [ "$build_target" = true ]; then
  if [ "$embench" = true ]; then
    echo "INFO: Building embench"
    ${SCRIPT_TARGET}/compile_embench_iot.sh $out $llvm $arch &>$out/embench_build.txt

    echo "INFO: Disassembling Binaries"
    ${SCRIPT_TARGET}/disassemble_embench_bins.sh $out $llvm
  fi

  if [ "$embench_2" = true ]; then
    echo "INFO: Building Embench-IoT 2.0"
    ${SCRIPT_TARGET}/compile_embench_2_0_iot.sh $out $llvm $arch &>$out/embench_build.txt

    echo "INFO: Disassembling Binaries for Embench-IoT 2.0"
    ${SCRIPT_TARGET}/disassemble_embench_2_0_bins.sh $out $llvm
  fi

  if [ "$fft" = true ]; then
    echo "INFO: Building FFT"
    ${SCRIPT_TARGET}/build_fft_etiss.sh $out $llvm $arch &>$out/fft_build.txt

    echo "INFO: Disassembling Binaries for FFT"
    ${SCRIPT_TARGET}/disassemble_fft.sh $out $llvm
  fi

  if [ "$cmsis" = true ]; then
    echo "INFO: Building cmsis"
    ${SCRIPT_TARGET}/compile_cmsis_dsp.sh &>${out}/cmsis_build.txt
  fi

  if [ "$musl" = true ]; then
    echo "INFO: Building musl"
    ${SCRIPT_TARGET}/compile_musl.sh &>${out}/musl_build.txt

    echo "INFO: Building bench for musl"
    echo "TODO: select bench" # maybe https://www.stupid-projects.com/posts/compile-benchmarks-with-gcc-musl-and-clang/ https://bitbucket.org/dimtass/gcc_musl_clang_benchmark/src/master/
  fi

  if [ "$linux" = true ]; then
    echo "INFO: Building linux"
    ${SCRIPT_TARGET}/compile_linux.sh $out $llvm &>${out}/linux_build.txt
  fi
fi

if [ "$run_target" = true ]; then
  if [ "$embench" = true ]; then
    if [ "$use_etiss" = true ]; then
      echo "INFO: Build Embench-IoT 1.0 for ETISS"
      ${SCRIPT_TARGET}/build_embench_for_etiss.sh $llvm $arch &>$out/build_embench_ETISS_out.txt

      echo "INFO: Disassemble ETISS Bins"
      ${SCRIPT_TARGET}/disassemble_embench_etiss_bins.sh $out $llvm

      echo "INFO: Generating the dynamic ETISS traces for Embench-iot"
      ${SCRIPT_TARGET}/execute_embench_etiss.sh $out &>${out}/dynamic_embench_ETISS_out.txt
    fi
    if [ "$use_spike" = true ]; then
      # echo "INFO: Building embench"
      # ${SCRIPT_TARGET}/compile_embench_iot.sh $out $llvm $arch &>$out/embench_build.txt

      echo "INFO: Generating the dynamic Spike traces for Embench-iot"
      ${SCRIPT_TARGET}/execute_embench.sh # &> ${out}/dynamic_embench_out.txt
    fi
  fi
  if [ "$embench_2" = true ]; then
    if [ "$use_etiss" = true ]; then
      echo "INFO: Build Embench-IoT 2.0 for ETISS"
      ${SCRIPT_TARGET}/build_embench_2_0_for_etiss.sh $llvm $arch &>$out/build_embench_ETISS_out.txt

      echo "INFO: Disassemble ETISS Bins"
      ${SCRIPT_TARGET}/disassemble_embench_2_0_etiss_bins.sh $out $llvm

      echo "INFO: Generating the dynamic ETISS traces for Embench-IoT 2.0"
      ${SCRIPT_TARGET}/execute_embench_2_0_etiss.sh $out &>${out}/dynamic_embench_ETISS_out.txt
    fi
    if [ "$use_spike" = true ]; then
      # echo "INFO: Building embench"
      # ${SCRIPT_TARGET}/compile_embench_iot.sh $out $llvm $arch &>$out/embench_build.txt

      echo "INFO: Generating the dynamic Spike traces for Embench-iot"
      ${SCRIPT_TARGET}/execute_embench_2_0.sh # &> ${out}/dynamic_embench_out.txt
    fi
  fi

  if [ "$fft" = true ]; then
    if [ "$use_etiss" = true ]; then
      echo "INFO: Build FFT for ETISS"
      ${SCRIPT_TARGET}/build_fft_etiss.sh $llvm $arch &>$out/build_embench_ETISS_out.txt

      echo "INFO: Disassemble FFT Bins"
      ${SCRIPT_TARGET}/disassemble_fft.sh $out $llvm

      echo "INFO: Generating the dynamic ETISS traces for FFT"
      ${SCRIPT_TARGET}/execute_arise_fft.sh $out &>${out}/dynamic_embench_ETISS_out.txt
    fi
  fi

  if [ "$cmsis" = true ]; then
    echo "INFO: Generating the dynamic traces for CMSIS-DSP"
    ${SCRIPT_TARGET}/execute_cmsisdsp.sh &>${out}/dynamic_cmsis_out.txt
  fi
fi

if [ "$analyze_binary" = true ]; then
  if [ "$embench" = true ]; then
    echo "INFO: Static analyzing the binaries of Embench-IoT"
    ${SCRIPT_TARGET}/static_analyze_embench.sh $out $llvm &>${out}/static_embench_out.txt
  fi

  if [ "$cmsis" = true ]; then
    echo "INFO: Disassembling Binaries"
    ${SCRIPT_TARGET}/disassemble_cmsis_dsp.sh $out

    echo "INFO: Static analyzing the binaries of cmsis"
    ${SCRIPT_ROOT}/static_analyze.sh $out &>${out}/static_cmsis_out.txt
  fi

  if [ "$musl" = true ]; then
    echo "INFO: Disassembling Binaries"
    ${SCRIPT_TARGET}/disassemble_musl_bins.sh $out $llvm

    echo "INFO: Static analyzing the binaries of musl"
    ${SCRIPT_ROOT}/static_analyze.sh $out &>${out}/static_musl_out.txt
  fi

  if [ "$linux" = true ]; then
    echo "INFO: Disassembling Binaries"
    ${SCRIPT_TARGET}/disassemble_linux_bins.sh $out $llvm

    echo "INFO: Static analyzing the linux binary"
    ${SCRIPT_ROOT}/static_analyze.sh out &>${out}/static_linux_out.txt
  fi
fi

if [ "$run_embench_size" = true ]; then
  echo "INFO: Executing the static size benchmark of Embench-iot"
  python3 ${SCRIPT_ROOT}/embench-iot/benchmark_size.py --json-output --json-comma &>${out}/embench_static_size.json
fi

if [ "$run_cpu" = true ]; then
  if [ "$embench" = true ]; then
    echo "INFO: building Embench-IoT 1.0 for CV32E40X"
    ${SCRIPT_TARGET}/compile_embench_for_cv32e40x.sh $llvm $arch &>${out}/build_embench_cv32e40x_log.txt

    echo "INFO: disassemble Embench-IoT 1.0"
    ${SCRIPT_TARGET}/disassemble_embench_bins.sh $out $llvm

    echo "INFO: executing Embench-IoT 1.0 in CV32E40X"
    ${SCRIPT_TARGET}/execute_embench_cv32e40x.sh $llvm $out &>${out}/execute_embench_cv32e40x_log.txt
  fi

  if [ "$embench_2" = true ]; then
    echo "INFO: building Embench-IoT 2.0 for CV32E40X"
    ${SCRIPT_TARGET}/compile_embench_2_0_for_cv32e40x.sh $llvm $arch &>${out}/build_embench_cv32e40x_log.txt

    echo "INFO: disassemble Embench-IoT 2.0"
    ${SCRIPT_TARGET}/disassemble_embench_2_0_bins.sh $out $llvm

    echo "INFO: executing Embench-IoT 2.0 in CV32E40X"
    ${SCRIPT_TARGET}/execute_embench_2_0_cv32e40x.sh $llvm $out &>${out}/execute_embench_cv32e40x_log.txt
  fi
fi

if [ "$entropy" = true ]; then
  echo "INFO: Analyzing binary entropy"

  if [ "$embench" = true ]; then
    ${SCRIPT_TARGET}/static_entropy.sh $out $llvm

  fi
  
  if [ "$embench_2" = true ]; then
    ${SCRIPT_TARGET}/static_entropy_embench_2.sh $out $llvm
  fi
fi


if [ "$analyze_traces" = true ]; then
  echo "INFO: Analyzing traces"
  cd ${out}
  TRACES=$(printf '%s ' *_trace.txt)
  cd ${SCRIPT_TARGET}
  # echo "  INFO Executing: python3 ${SCRIPT_TARGET}/seal/analysis/dynamic/main.py --path ${out} ${TRACES}"
  python3 ${SCRIPT_ANALYSIS}/dynamic.py --path ${out} ${TRACES} &>${out}/dynamic_analysis_out.txt
fi

if [ "$generate_insts" = true ]; then
  echo "INFO: Generating Instructions"
  cd ${out}
  TRACES=$(printf '%s ' *_trace.txt)
  cd ${SCRIPT_TARGET}
  echo "  INFO Executing: ${SCRIPT_ROOT}/gen_insts.sh $out"
  ${SCRIPT_ROOT}/gen_insts.sh $out &>${out}/generate_insts_out.txt
fi

cd ${SCRIPT_TARGET}
