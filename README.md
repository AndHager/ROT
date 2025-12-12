# Sizalizer: A Multi-layer Analysis Framework for ISA Optimization

Sizalizer is an innovative analysis framework designed to advance the development of embedded C/C++ applications alongside RISC-V instruction set extensions. 

## Prerequisites

It is tested on Ubuntu 22.04


### Tools

- git 
- cmake 
- make 
- gcc 
- g++ 
- docker
- binwalk
- readelf
- objdump
- time (explicitly installed not the bash func)
- python3
- pip3
- spike
- etiss


### Python libs



```bash
virtualenv -p python3 venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

- pathlib
- pyparsing
- numpy
- matplotlib
- neo4j
- enum
- tikzplotlib

#### Fixes

Fix the (issue)[https://github.com/nschloe/tikzplotlib/issues/559] of tikzplotlib with matplotlib > 3.6 
Replace `mpl.common_texification` with `mpl._tex_escape` in `~/.local/lib/python3.<XX>/site-packages/tikzplotlib/_axes.py`.
Because matplotlib 3.6 deprecates `pgf.common_texification`.


### Manually install

Graph DB and tools:

- memgraph graph db (https://memgraph.com/docs/getting-started)
- mgclient (https://github.com/memgraph/mgclient)
- mgconsole (https://github.com/memgraph/mgconsole)

Coss Compiler X86 -> RV32

- Prebuild RISC-V toolchain (https://github.com/riscv-collab/riscv-gnu-toolchain/releases/download/2024.03.01/riscv32-elf-ubuntu-22.04-llvm-nightly-2024.03.01-nightly.tar.gz)
- Manually build clang version 18.1.3: (https://github.com/llvm/llvm-project/releases/tag/llvmorg-18.1.3)

Linux kernel

- Source of linux kernel (https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.8.9.tar.xz)

Musl libc

- Source of musl libc (https://git.musl-libc.org/cgit/musl/snapshot/musl-1.2.5.tar.gz)

ETISS

- Source of ETISS Instruction Set Simulator (https://github.com/tum-ei-eda/etiss)


## Setup

Build memgraph container:

```bash
docker run -p 7687:7687 -p 7444:7444 -p 3000:3000 --name memgraph memgraph/memgraph-platform
```

Build LLVM CDFG pass with:

```bash
cd llvm-pass-plugin
mkdir -p build
cd build
cmake ..
make
cd ../..
```

## Architecture

[Sizalizer Architecture](img/ArchitekturMatrix.drawio.pdf)

## Usage

Use the `bax.sh` script in order to execute the analysis process.

```bash
Usage: bax.sh [OPTIONS]

This script builds and executes the Analysis for Embench-iot.

Available options:

    --clean               Clean run full analysis (default: false)

    --musl                Set target to musl (default: false)
    --embench             Set target to Embench-IoT 1.0 (default: false)
    --embench-2           Set target to Embench-IoT 2.0  (default: false)
    --cmsis               Set target to CMSIS (default: false)
    --linux               Set target to Linux (default: false)
    --fft                 Set target to FFT (default: false)

    --out                 Set out dir (default: /home/ahc/Desktop/CodeComp/integrator/out)
    --llvm                Set llvm path (default: /home/ahc/riscv/bin/)
    --arch                Set arch (default: rv32gc_xarise)

    --start-db            Start the database service (default: false)
    --purge-db            Purge the database (default: false)
    --build-cpu           Build the cv32e40x core (default: false)
    --build-dfg           Build the data flow graph (default: false)
    --analyze-dfg         Analyze the data flow graph (default: false)
    --build-target        Build target (default: false)
    --analyze-binary      Analyze binary files (default: false)
    --run-embench-size    Run Embench benchmark for size (default: false)
    --run-target          Run target in simulator (spike/ETISS) (default: false)
    --use-etiss           Run target in ETISS (default: false) 
    --use-spike           Run target in spike (default: false) 
    --run-cpu             Run target in cv32e40x core (default: false)
    --entropy             Entropy analysis (default: false)
    --analyze-traces      Enable trace analysis (default: false)
    --generate-insts      Enable instruction generation (default: false)
    --help                Display this help and exit
```


### Memgraph

Used to store the CDFG

#### Start memgraph seperatly

```bash
docker start memgraph
```

Web interface available at: `http://localhost:3000/`

##### Standard graph style

Memgraph graph style:

```
@NodeStyle {
  size: 3
  label: Property(node, "name")
  border-width: 1
  border-color: #ffffff
  shadow-color: #333333
  shadow-size: 20
}

@EdgeStyle {
  width: 0.4
  label: Type(edge)
  arrow-size: 1
  color: #6AA84F
}
```

##### Some Queries

Get whole Graph:

```
MATCH p=(n)-[r]-(m)
RETURN *;
```

Get chains of equal instructions (excluding const):

```
MATCH (n)
MATCH (m)
WHERE (NOT n.name = 'Const') AND (NOT m.name = 'Const') AND n.name = m.name
MATCH p=(n)-[r:DFG]-(m)
RETURN *;
```

Get matching pairs of instructions:

```
MATCH (n1) 
MATCH (m1)
MATCH (n2)
MATCH (m2)
MATCH p1=(n1)-[r1:DFG]->(m1)
MATCH p2=(n2)-[r2:DFG]->(m2)
WHERE (NOT n1.name = 'Const') AND (NOT m1.name = 'Const') AND n1.name = n2.name AND m1.name = m2.name AND n1 != n2 AND m1 != m2
RETURN *;
```

Get matching triples of instructions:

```
MATCH p1=(n1)-[r1:DFG]->(m1)-[i1:DFG]->(j1)
MATCH p2=(n2)-[r2:DFG]->(m2)-[i2:DFG]->(j2)
WHERE ((NOT n1.name = 'Const') AND (NOT m1.name = 'Const') AND (NOT j1.name = 'Const')
    AND (NOT n1.name = 'phi') AND (NOT m1.name = 'phi') AND (NOT j1.name = 'phi')
    AND (NOT n1.name = 'call') AND (NOT m1.name = 'call') AND (NOT j1.name = 'call')
    AND n1.name = n2.name AND m1.name = m2.name AND j1.name = j2.name 
    AND n1 != n2 AND m1 != m2 AND j1 != j2)
RETURN p1;
```

Get load -> X -> store triplet:
```
MATCH p=(n0)-[:DFG]->(n1)-[:DFG]->(n2)
WHERE (
  NOT n0.name = 'Const' 
  AND NOT n1.name = 'Const' 
  AND NOT n2.name = 'Const'
  AND n0.name = 'load'
  AND n2.name = 'store'
)
RETURN p;
```


### Usage of LLVM CDFG generation Pass

```sh
$ clang -O3 -fpass-plugin=./build/libLLVMCDFG.so ...
```



### DFG Analysis

The DFG analysis can be conducted separately:

```
usage: analysis/dfg.py [-h] [--host [HOST]] [--port [PORT]] [--pdc [PDC]] [--clear-db [CLEAR_DB]]

Analyze the File.

options:
  -h, --help            show this help message and exit
  --host [HOST]         host of the memgraph (or Neo4j) DB (reachable over bolt)
  --port [PORT]         port of the Memgraph DB
  --pdc [PDC]           Plot Duplicated Chains
  --clear-db [CLEAR_DB] Clear the Database
```


### Binary Analysis

You may want to use the binary analysis script separately:

```
usage: analysis/static.py [-h] [--path PATH] F [F ...]

Count the instructions in an assembly file.

positional arguments:
  F            files to analyze

options:
  -h, --help   show this help message and exit
  --path PATH  base path for the files
```


### Trace Analysis

The DFG analysis can be conducted separately:

```
usage: dynamic.py [-h] [--path PATH] [--spike SPIKE] [--etiss ETISS] F [F ...]

Count the instructions in an trace file.

positional arguments:
  F              files to analyze

options:
  -h, --help     show this help message and exit
  --path PATH    base path for the files
  --spike SPIKE  Use the Spike trace file parser
  --etiss ETISS  Use the ETISS trace file parser
```


# Spike

Config Spike:

```bash
../configure --prefix=${RISCV_TOOLCHAIN_PATH} --with-isa=rv32gc_zifencei
```


Config RISC-V PK:

```bash
CC=${RISCV_TOOLCHAIN_PATH}/bin/riscv32-unknown-elf-gcc CXX=${RISCV_TOOLCHAIN_PATH}/bin/riscv32-unknown-elf-g++ OBJCOPY=${RISCV_TOOLCHAIN_PATH}/bin/riscv32-unknown-elf-objcopy ../configure --bindir=${RISCV_TOOLCHAIN_PATH} --host=riscv32-unknown-elf --with-arch=rv32gc_zifencei --with-abi=ilp32 --prefix=${RISCV_TOOLCHAIN_PATH}
```

Run Spike with:

```bash
$Integrator_Base/riscv-isa-sim/build/spike $Integrator_Base/riscv-isa-sim/riscv-pk/build/pk <Target>
```


# ARISE

ARISE (Automating RISC-V Instruction Set Extension) automates the generation of RISC-V instructions based on assembly patterns, which are selected by an extendable set of metrics.

## Architecture

[ARISE Architecture](img/ARISE_Architecture.drawio.pdf)

## Usage

```bash
usage: generator.py [-h] [--static STATIC] [--dynamic DYNAMIC] [--size SIZE] [--count COUNT] [--time TIME]
                    [--csv CSV] [--results RESULTS] [--path PATH] [--debug DEBUG]
                    F [F ...]

Generate new Instructions.

positional arguments:
  F                  files as basis for instruction generation

options:
  -h, --help         show this help message and exit
  --static STATIC    Generate based on static insts
  --dynamic DYNAMIC  Generate based on dynamic insts
  --size SIZE        Generate based on size optimization
  --count COUNT      Generate based on instr count optimization
  --time TIME        Measure exe time
  --csv CSV          Print time in CSV
  --results RESULTS  Print results
  --path PATH        base path for the files
  --debug DEBUG      print debug messages
```

# Scripts


This project contains many helper bash scripts. Short descriptions:

- eval_arise.sh — Run ARISE evaluation pipeline: process core_desc files, build Seal5, patch & build ETISS, compile/disassemble/execute Embench targets and collect results.
- build_etiss.sh — Configure, build and install ETISS into etiss/etiss_arise.
- build_cpu.sh — Build the cv32e40x core with Verilator.

Target scripts (target_scripts/):
- build_cmsisdsp_for_etiss.sh — Build CMSIS-DSP examples for ETISS.
- build_embench_2_0_for_etiss.sh — Build Embench-IoT 2.0 for ETISS.
- build_embench_for_etiss.sh — Build Embench-IoT 1.x for ETISS.
- build_fft_etiss.sh — Build FFT benchmark for ETISS.

- compile_cmsis_dsp.sh — Compile CMSIS-DSP benchmarks for the chosen toolchain.
- compile_embench_2_0_for_cv32e40x.sh — Compile Embench 2.0 for the cv32e40x core.
- compile_embench_2_0_iot.sh — Compile Embench-IoT 2.0 suite.
- compile_embench_for_cv32e40x.sh — Compile Embench 1.x for the cv32e40x core.
- compile_embench_iot_asm.sh — Compile Embench IoT benchmarks producing assembly outputs.
- compile_embench_iot.sh — Compile Embench IoT benchmarks.
- compile_linux.sh — Build Linux kernel/userland targets (helper wrapper).
- compile_musl.sh — Compile targets against musl libc.

- disassemble_cmsis_dsp.sh — Disassemble CMSIS-DSP binaries.
- disassemble_embench_2_0_bins.sh — Disassemble Embench 2.0 binaries.
- disassemble_embench_2_0_etiss_bins.sh — Disassemble Embench 2.0 ETISS-run binaries.
- disassemble_embench_bins.sh — Disassemble Embench 1.x binaries.
- disassemble_embench_etiss_bins.sh — Disassemble Embench 1.x ETISS-run binaries.
- disassemble_fft.sh — Disassemble FFT benchmark binaries.
- disassemble_linux_bins.sh — Disassemble Linux target binaries.
- disassemble_musl_bins.sh — Disassemble musl-built binaries.

- eval_power.sh — Run power evaluation workflows / measurements.

- execute_arise_embench_2_0.sh — Execute ARISE-generated binaries for Embench 2.0.
- execute_arise_embench.sh — Execute ARISE-generated binaries for Embench 1.x.
- execute_arise_fft.sh — Execute ARISE FFT binaries.
- execute_cmsisdsp.sh — Run CMSIS-DSP benchmark executables.
- execute_embench_2_0_cv32e40x.sh — Run Embench 2.0 on cv32e40x simulation.
- execute_embench_2_0_etiss.sh — Run Embench 2.0 on ETISS.
- execute_embench_2_0.sh — Run Embench 2.0 on the configured simulator.
- execute_embench_cv32e40x.sh — Run Embench 1.x on cv32e40x simulation.
- execute_embench_etiss.sh — Run Embench 1.x on ETISS.
- execute_embench.sh — Run Embench 1.x on the configured simulator.

- static_analyze_embench.sh — Run static instruction analysis for Embench benchmarks.
- static_dfg_analyze_cmsis_dsp.sh — Perform DFG analysis for CMSIS-DSP code.
- static_dfg_analyze_embench_2_0_iot.sh — Perform DFG analysis for Embench 2.0 IoT.
- static_dfg_analyze_embench_iot.sh — Perform DFG analysis for Embench IoT.
- static_dfg_analyze_linux.sh — Perform DFG analysis for Linux targets.
- static_dfg_analyze_musl.sh — Perform DFG analysis for musl-built targets.

- static_entropy_embench_2.sh — Run entropy analysis for Embench 2.0 results.
- static_entropy.sh — General entropy analysis helper.
- static_generate_inst.sh — Generate instruction candidates statically (used by ARISE).


