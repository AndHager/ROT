import os
import argparse
from pathlib import Path
import typing
import string
from enum import Enum

import static
import dynamic
import generator
from tools import parse_utils, evaluator
from model import register, instruction_model, immediate


ignore = generator.ignore


def eval_etiss_line(source_line: str, ignore, count: bool) -> int:
    if source_line[0:2] == '0x':

        elems = source_line.split(' ')
        
        if elems[1] in ignore['mnemonic']:
            return 0
        elif count:
            return 1
        else:
            opcode = elems[3]
            oplen = len(opcode)
            assert (oplen % 16) == 0
            return oplen / 8
    return 0


def eval_spike_line(source_line: str, ignore, count: bool) -> int:
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
                return 0
            opcode = elems[1]
            if int(opcode, 16) & ignore['opcode'] > 0:
                return 0
            elif count:
                return 1
            else:
                if mnemonic[0:2] == 'c.':
                    return 2
                elif len(opcode) == 12:
                    return 6
                else:
                    return 4 
    return 0


def parse_line(source_line: str, ignore, count: bool) -> int:
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
                
            mnemonic = elems[mn_index]
            
            if mnemonic.replace('c.', '') in ignore['mnemonic']:
                return 0
            
            if count:
                return 1
            if len(opcode) % 2 != 0:
                print(source_line)
                print(opcode)
            assert len(opcode) % 2 == 0
            return len(opcode) / 2
            
    return 0


def main(args):
    '''
    The main entry point for the script that generates Instructions.

    This function takes command-line arguments, extracts instructions from each provided file,
    performs the instruction generation, selection and evaluation.

    Parameters:
    args (argparse.Namespace): command-line arguments.
                                It must have at least the following attributes:
                                - path: The base path where the asm files are located.
                                - files: An iterable with the names of the asm to be processed.

    '''
    path = str(Path(args.path).absolute())
    debug = args.debug
    static_file = args.static
    dynamic_file = args.dynamic
    size = args.size
    count  = args.count
    spike = args.spike
    fact = args.fact
    
    total_base = 0
    total_new = 0
    
    mn_ign = []
    # mn_ign += instruction_model.load + instruction_model.store + ignore
    
    ign = {
        'mnemonic': mn_ign,
        'opcode': 0xFF000000
    }
    
    if debug:
        print('Base Path: ', path)
        
    parser = parse_line
    if dynamic_file:
        parser = eval_etiss_line
        if spike:
            parser = eval_spike_line

    file_vals: list[int] = []
    for file in args.files:
        if debug:
            print('File to analyze: ', file)

        fqpn = '{}/{}'.format(str(path), str(file))
        # fqpn = fqpn.replace('_trace.txt', '.asm')
        
        file_vals.append(parse_utils.parse_val_cnt(
            fqpn, 
            parser, 
            ign,
            static_file,
            count
        ))
    base_val = file_vals[0]
    assert base_val > 0
    
    ty = 'Static'
    if dynamic_file: ty = 'Dynamic'
    method = 'Size'
    unit = 'byte'
    if count: 
        method = 'Count'
        unit = 'Inst'
    print(ty, method, 'Improvement', args.files[0], ': ', base_val, unit)
    
    for i in range(1, len(file_vals)):
        val = file_vals[i]
        assert val > 0
        
        
        ext = ''
        if ty == 'Static':
            result = int(base_val - val)
            ext = 'Byte'
        else:
            if fact:
                result = base_val/val
                ext = 'x'
            else:
                result = (val/base_val - 1)*100
                ext = '%'
            
            result = round(result, 2)
        print('  ', args.files[i], ': ', val, unit, '; ', result, ext)
        

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate new Instructions.')
    parser.add_argument('files', metavar='F', type=str, nargs='+', help='files as basis for instruction generation')
    parser.add_argument('--static', type=bool, default=False, help='Generate based on static insts')
    parser.add_argument('--dynamic', type=bool, default=False, help='Generate based on dynamic insts')
    parser.add_argument('--size', type=bool, default=False, help='Generate based on size optimization')
    parser.add_argument('--count', type=bool, default=False, help='Generate based on instr count optimization')
    parser.add_argument('--spike', type=bool, default=False, help='Generate based on spike')
    parser.add_argument('--fact', type=bool, default=False, help='factor results')
    
    parser.add_argument('--path', type=str, help='base path for the files') 
    parser.add_argument('--debug', type=bool, help='print debug messages')

    main(parser.parse_args())

