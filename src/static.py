import argparse
from pathlib import Path
import string

import generator

from model import instruction_model, program
from tools import parse_utils, evaluator, modes, plotter

# Debug logs (very verbose)
debug = False
# Define if each asm file should be evaluated speratly or in total
plot_all = False

import re
from enum import Enum

from dataclasses import dataclass
from typing import Optional, List


class AssemblyLineType(Enum):
    DISASSEMBLED = 1
    COMPILED = 2

@dataclass
class AssemblyLine:
    type: AssemblyLineType
    address: Optional[str] = None
    opcode: Optional[str] = None
    instruction: str = None
    arguments: List[str] = None
    jumplabel: Optional[str] = None
    comment: Optional[str] = None

def parse_assembly_line(source_line):
    line = re.sub(r'\s+', ' ', source_line).strip() # reduces multiple spaces or tabs to one space
    
    line_type = AssemblyLineType.DISASSEMBLED if ":" in line else AssemblyLineType.COMPILED     
    parsedLine = AssemblyLine(line_type)

    if line.startswith(".cfi"):
      # Annotation code should not be included
      return

    comment = ""
    address = ""
    machine_code = ""
    jumplabel = ""
    
    line = line.replace(", ", ",")
    if "#" in line:
        line, comment = line.strip().split("#")
        parsedLine.comment = comment.strip()
    if "<" in line:
        line, jumplabel = line.strip().split("<")
        jumplabel = "<" + jumplabel
        parsedLine.jumplabel = jumplabel.strip()
    
    if not "ret" and not "nop" in line:
        line, arguments = line.strip().rsplit(" ", 1)
        arguments = arguments.replace("(",",").replace(")", "")
        if "," in arguments:
            arguments = arguments.split(",")  
    else:
        arguments = []

    parsedLine.arguments = arguments
    
    # line is disassembled output
    if line_type == AssemblyLineType.DISASSEMBLED:
        line, instruction = line.strip().rsplit(" ", 1)
        address, machine_code = line.strip().split(":")
        parsedLine.instruction = instruction.strip()
        parsedLine.address = address.strip()
        
        machine_code = machine_code.strip()
        # address is reversed with seperate bytes
        if " " in machine_code:
            machine_code = machine_code.split(" ")
            machine_code.reverse()
            machine_code = "".join(machine_code)

        parsedLine.opcode = machine_code
    else:
        instruction = line
        parsedLine.instruction = instruction.strip()

    return parsedLine

def parse_line(source_line: str, ignore) -> instruction_model.Instruction:
    '''
    Parses a line of assembly code into an instruction object.

    This function is designed to parse a single line of assembly code provided as 
    a string in the intel format of llvm-objdump.
    It expects the source line to contain an address, a mnemonic, and an opcode, and params 
    each separated by spaces. Each component is then extracted and used to construct
    an `Instruction` object from the `instruction_model` module.
    Additionally, the function parses up to three parameters.
    <address> <opcode> <mnemonic> <params>, ...

    For Example:
    00000094 <.LBB0_11>:
          94: 08 40        	c.lw	a0, 0x0(s0)
          96: 13 65 05 08  	ori	    a0, a0, 0x80
          9a: 08 c0        	c.sw	a0, 0x0(s0)

    Parameters:
    - source_line (str): A string representing a single line of assembly code.

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
    
    if source_line[0:1] == ' ' or source_line[0:1] in string.hexdigits:
        elems: list[str] = source_line.strip() \
            .replace('    ', ' ~ ') \
            .replace('\t', ' ') \
            .replace('  ', ' ') \
            .replace('  ', ' ') \
            .replace('  ', ' ') \
            .replace(',', '') \
            .replace(':', '') \
            .replace(')', '') \
            .replace('{', '') \
            .replace('}', '') \
            .replace('(', ' ') \
            .split(' ')
        elen = len(elems)
        if elen >= 6:
            mn_index = 5
            if elen > 8 and elems[8][0:2] == 'k.':
                mn_index = 8
            
            opcode = elems[1]
            oplen = len(opcode)
            if oplen >= 4:
                mn_index = 4
                if oplen == 8:
                    mn_index = 3
                    
            else:
                op_elems = elems[1:mn_index]
                op_elems.reverse()
                opcode = ''.join(op_elems).replace('~', '')
                
            instruction = instruction_model.Instruction(
                address=elems[0], 
                opcode=opcode, 
                mnemonic=elems[mn_index]
            )
            if instruction.get_base_mnemonic() in ignore['mnemonic']:
                return None

            for elem in elems[(mn_index+1):]:
                instruction.append_param(elem)
            
            # print("Parsed inst:", instruction)
            return instruction
    return None



def main(args):
    '''
    The main entry point for the script that processes and analyzes files.

    This function takes command-line arguments, extracts instructions from each provided file,
    performs the evaluation, generates plots, and prints static code size toghether with the improvement oportunity.

    Parameters:
    args (argparse.Namespace): command-line arguments.
                                It must have at least the following attributes:
                                - path: The base path where the asm files are located.
                                - files: An iterable with the names of the asm to be processed.

    '''
    
    ign = {
        'mnemonic': instruction_model.load + instruction_model.store + generator.ignore,
        'opcode': 0x80000000
    }
    path = str(Path(args.path).absolute())
    tp = 'Static'
    total = []
    for file in args.files:
        if debug:
            print('Base Path: ', path)
            print('File to analyze: ', file)


        fqpn = '{}/{}'.format(str(path), str(file))
        program: program.Program = parse_utils.parse_file(fqpn, parse_line, ign)
        if len(program.instructions) > 0:
            total += program.instructions
            if plot_all:
                evaluator.plot_individual_static_stats(file, program.instructions, tp, path)
            evaluator.print_individual_static_improvement(file, program.instructions)
        else:
            print('ERROR: No instructions in', fqpn)
    
    if len(total) > 1:
        evaluator.print_total_static_improvement(total)
        
        for mode in modes.Mode:
            stats = evaluator.most_inst(total, mode, modes.SearchKey.MNEMONIC, 10)
            plotter.plot_bars(stats, '_Total', tp, path, mode, modes.SearchKey.MNEMONIC)

        stats = evaluator.most_inst(total, modes.Mode.ALL, modes.SearchKey.OPCODE, 10)
        plotter.plot_bars(stats, '_Total', tp, path, modes.Mode.ALL, modes.SearchKey.OPCODE)

        stats = evaluator.most_inst(total, modes.Mode.ALL, modes.SearchKey.REGISTER, 10)
        plotter.plot_bars(stats, '_Total', tp, path, modes.Mode.ALL, modes.SearchKey.REGISTER)
        
        chains = evaluator.longest_chains(total, 10)
        plotter.plot_bars(chains, '_Total', tp, path, modes.Mode.ALL, modes.SearchKey.CHAIN)

        chains = evaluator.chain_distrib(total, 10)
        plotter.plot_bars(chains, '_Total', tp, path, modes.Mode.ALL, modes.SearchKey.CHAIN_DISTRIB)

        triplets = evaluator.most_triplets(total, 10, equal=False, connected=True)
        plotter.plot_bars(triplets, '_Total', tp, path, modes.Mode.ALL, modes.SearchKey.TRIPLET)

        triplets = evaluator.most_triplets(total, 10)
        plotter.plot_bars(triplets, '_Total_Free', tp, path, modes.Mode.ALL, modes.SearchKey.TRIPLET)

        lw16_imp = evaluator.get_lswm_improvement(total, base_isnt='lw', new_byte_count=2, base_regs=['sp', 's0', 's1', 'a0', 'a1', 'a2', 'a3', 'a4'], dest_regs=['ra', 'sp', 's0', 's1', 'a0', 'a1'])
        sw16_imp = evaluator.get_lswm_improvement(total, base_isnt='sw', new_byte_count=2, base_regs=['sp', 's0', 's1', 'a0', 'a1', 'a2', 'a3', 'a4'], dest_regs=['ra', 'sp', 's0', 's1', 'a0', 'a1'])
        
        lw32_imp = evaluator.get_lswm_improvement(total, base_isnt='lw', new_byte_count=4, base_regs='all', dest_regs={'ra', 'sp', 's0', 's1', 'a0', 'a1', 'a2', 'a3', 'a4', 'a5', 's2', 's3', 's4', 's5', 's6', 's7'})
        sw32_imp = evaluator.get_lswm_improvement(total, base_isnt='sw', new_byte_count=4, base_regs='all', dest_regs={'ra', 'sp', 's0', 's1', 'a0', 'a1', 'a2', 'a3', 'a4', 'a5', 's2', 's3', 's4', 's5', 's6', 's7'})
        
        lw48_imp = evaluator.get_lswm_improvement(total, base_isnt='lw', new_byte_count=6, base_regs='all', dest_regs='all')
        sw48_imp = evaluator.get_lswm_improvement(total, base_isnt='sw', new_byte_count=6, base_regs='all', dest_regs='all')


        call = evaluator.get_en_improvement(total, ['auipc', 'jalr'])
        eli_imp = evaluator.get_en_improvement(total, ['lui', 'addi'])
        e2addi_imp = evaluator.get_en_improvement(total, ['addi', 'addi'])
        e2add_imp = evaluator.get_en_improvement(total, ['add', 'add'])
        
        e3add_imp = evaluator.get_en_improvement(total, ['srli', 'slli', 'or'])

        total_byte_count = evaluator.get_byte_count(total)
        imp = [
            ('e.call', evaluator.rel(call, total_byte_count)),
            ('e.li', evaluator.rel(eli_imp, total_byte_count)),
            ('e.2addi', evaluator.rel(e2addi_imp, total_byte_count)),
            ('e.2add', evaluator.rel(e2add_imp, total_byte_count)),
            ('e.slro', evaluator.rel(e3add_imp, total_byte_count)),
            ('c.lwm', evaluator.rel(lw16_imp, total_byte_count)),
            ('c.swm', evaluator.rel(sw16_imp, total_byte_count)),
            ('lwm', evaluator.rel(lw32_imp, total_byte_count)),
            ('swm', evaluator.rel(sw32_imp, total_byte_count)),
            ('e.lwm', evaluator.rel(lw48_imp, total_byte_count)),
            ('e.swm', evaluator.rel(sw48_imp, total_byte_count)),
        ]
        plotter.plot_bars(imp, '_Total_LSWM_IMP', tp, path, modes.Mode.ALL, modes.SearchKey.MNEMONIC)

        pairs = evaluator.most_pairs(total, 10, equal=False, connected=True)
        plotter.plot_bars(pairs, '_Total', tp, path, modes.Mode.ALL, modes.SearchKey.PAIR)

        pairs = evaluator.most_pairs(total, 10)
        plotter.plot_bars(pairs, '_Total_Free', tp, path, modes.Mode.ALL, modes.SearchKey.PAIR)

    else:
        print('ERROR: In total no instructions')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Count the instructions in an assembly file.')
    parser.add_argument('files', metavar='F', type=str, nargs='+', help='files to analyze')
    parser.add_argument('--path', type=str, help='base path for the files')

    main(parser.parse_args())
