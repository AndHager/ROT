import argparse
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from model import instruction_model, program
import string

import generator

from tools import parse_utils, evaluator, modes, plotter

plt.rcParams["font.family"] = "cmb10"

debug = False
plot_all = False


def get_etiss_addr(source_line: str) -> int:
    if source_line[0:2] == '0x':
        return int(source_line[0:18], 16)
    return 0


def parse_etiss_line(source_line: str, ignore) -> instruction_model.Instruction:
    """
    Parses a trace code line into an instruction object.

    This function is designed to parse a single trace code line provided as 
    a string in the trace format of ETISS.
    It expects the source line to contain an address, a mnemonic, and an opcode, and params 
    each separated by spaces. Each component is then extracted and used to construct
    an `Instruction` object from the `instruction_model` module.
    Additionally, the function parses up to three parameters that follow the opcode.
    Each parameter is assumed to be separated by spaces and optionally enclosed in 
    brackets, which are stripped if present.
    <address>: <mnemonic> # <opcode> [<param>=<value> | *]

    For Example:
    0x0000000010000c02: addi # 10000010100000011000011000010011 [rd=12 | rs1=3 | imm=2088]
    0x0000000010000c06: csub # 1000111000001001 [rs2=2 | rd=4]
    0x0000000010000c08: cjal # 0010010000000101 [imm=544].

    Parameters:
    - source_line (str): A string representing a single line of trace code.

    Returns:
    - `Instruction`: An Instruction object populated with the parsed data, or
      `None` if the source line does not start with '0x' or fails to parse.

    Note:
    - The function contains an undeclared variable `debug`. If `debug` is `True`, 
      it prints all source lines a message when the source line does not start with '0x' but does 
      not raise a `NameError`.
    - The global `instruction_model` with an `Instruction` class should be available
      in the context where this function is executed.
    """
    if source_line[0:2] == '0x':

        elems = source_line.split(' ')
        elen = len(elems)

        address = elems[0][2:-1]
        mnemonic = elems[1]
        
        if mnemonic in ignore['mnemonic']:
            return None
        
        opcode = elems[3]

        instruction = instruction_model.Instruction(address, opcode, mnemonic)

        if elen > 4:
            first_param = elems[4][1:]
            instruction.regs.append(first_param)

        
        if elen > 6:
            second_param = elems[6]
            if elen == 7:
                second_param = second_param[:-1]
            instruction.regs.append(second_param)

        if elen > 8:
            third_param = elems[8][:-1]
            instruction.regs.append(third_param)
        
        if debug:
            print(str(instruction))
        return instruction
    if debug:
        print('No Inst:', source_line)
    return None


def get_spike_addr(source_line: str) -> int:
    if source_line[0:12] == 'core   0: 0x':
        return int(source_line[12:20], 16)
    return 0
 

def parse_spike_line(source_line: str, ignore) -> instruction_model.Instruction:
    '''
    Parses a line of sparke trace into an instruction object.
    
    Parameters:
    - source_line (str): A string representing a single line.

    Returns:
    - `Instruction`: An Instruction object populated with the parsed data, or
      `None` if the source line does not start with '0x' or fails to parse.

    Note:
    - The function contains an undeclared variable `debug`. If `debug` is `True`, 
      it prints all source lines a message when the source line does not start with '0x' but does 
      not raise a `NameError`.
    - The global `instruction_model` with an `Instruction` class should be available
      in the context where this function is executed.
    '''
    if source_line[0:12] == 'core   0: 0x':
        elems: list[str] = source_line[10:].strip() \
            .replace(')', '') \
            .replace('(', ' ') \
            .replace('\t', ' ') \
            .replace(' - ', '-') \
            .replace(' + ', '+') \
            .replace('  ', ' ') \
            .replace('  ', ' ') \
            .replace('  ', ' ') \
            .replace(',', '') \
            .replace(':', '') \
            .split(' ')
        elen = len(elems)
        if elen >= 3:
            mnemonic = elems[2]
            if mnemonic in ignore['mnemonic']:
                return None
            opcode = elems[1]
            if int(opcode, 16) & ignore['opcode'] > 0:
                return None
            instruction = instruction_model.Instruction(
                address=elems[0], 
                opcode=opcode, 
                mnemonic=mnemonic
            )

            for elem in elems[3:]:
                instruction.append_param(elem)
            
            return instruction
    return None


def main(args):
    """
    The main entry point for the script that processes and analyzes files.

    This function takes command-line arguments, extracts instructions from each provided file,
    performs the evaluation, generates plots, and prints dynamic code size toghether with the improvement oportunity.

    Parameters:
    args (argparse.Namespace): command-line arguments.
                                It must have at least the following attributes:
                                - path: The base path where the traces are located.
                                - files: An iterable with the names of the traces to be processed.

    """
    ign = {
        'mnemonic': instruction_model.load + instruction_model.store + generator.ignore,
        'opcode': 0x80000000
    }
    path = Path(args.path).absolute()
    use_spike = args.spike
    use_etiss = args.etiss
    
    parser = parse_spike_line
    if use_etiss: 
        parser = parse_etiss_line
    
    tp = 'Dynamic'
    total = []
    for file in args.files:
        if debug:
            print('Base Path: ', path)
            print('File to analyze: ', file)


       
        fqpn = '{}/{}'.format(str(path), str(file))
        program = parse_utils.parse_file(fqpn, parser, ign)
        instructions = program.instructions
        if debug:
            for inst in instructions:
                print(inst)
        total += instructions
        
        if plot_all:
            evaluator.plot_individual_dynamic_stats(file, instructions, tp, path)
        evaluator.print_individual_dynamic_improvement(file, instructions)

    evaluator.print_total_dynamic_improvement(total)

    for mode in modes.Mode:
        stats = evaluator.most_inst(total, mode, modes.SearchKey.MNEMONIC, 10)
        plotter.plot_bars(stats, '_Total', tp, path, mode, modes.SearchKey.MNEMONIC, True)

    stats = evaluator.most_inst(total, modes.Mode.ALL, modes.SearchKey.OPCODE, 10)
    plotter.plot_bars(stats, '_Total', tp, path, modes.Mode.ALL, modes.SearchKey.OPCODE, True)

    stats = evaluator.most_inst(total, modes.Mode.ALL, modes.SearchKey.REGISTER, 10)
    plotter.plot_bars(stats, '_Total', tp, path, modes.Mode.ALL, modes.SearchKey.REGISTER, True)
    
    # chains = evaluator.longest_chains(total, 10)
    # plotter.plot_bars(chains, '_Total', tp, path, modes.Mode.ALL, modes.SearchKey.CHAIN, True)

    # addi_dist = evaluator.inst_vals(total, 'addi', 10)
    # plotter.plot_bars(addi_dist, '_Total_ADDI', tp, path, modes.Mode.FULL, modes.SearchKey.IMM)

    # lw_dist = evaluator.inst_vals(total, 'lw', 10)
    # plotter.plot_bars(lw_dist, '_Total_LW', tp, path, modes.Mode.FULL, modes.SearchKey.IMM)

    pairs = evaluator.most_pairs(total, 10, equal=False, connected=True)
    plotter.plot_bars(pairs, '_Total', tp, path, modes.Mode.ALL, modes.SearchKey.PAIR, True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Count the instructions in an trace file.')
    parser.add_argument('files', metavar='F', type=str, nargs='+', help='files to analyze')
    parser.add_argument('--path', type=str, help='base path for the files')
    parser.add_argument('--spike', type=bool, default=True, required=False, help='Use the Spike trace file parser')
    parser.add_argument('--etiss', type=bool, default=False, required=False, help='Use the ETISS trace file parser')


    main(parser.parse_args())

