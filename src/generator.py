import os
import argparse
from pathlib import Path
import typing
from enum import Enum
from time import perf_counter_ns

import static
import dynamic
from tools import parse_utils, evaluator
from model import register, instruction_model, immediate

NANO_TO_MICOR = 1000

ONLY_ONE_IMM = True

BASE_OP_LEN = 7
CUST_OP_LEN = 2

base_32_opcodes = [
    '0001011',
    '0101011',
    '1010111',
    '1110111'
]

reserved_32_opcodes = [
    '1101011',
    '1010111',
    '1110111'
]

base_48_opcodes = [
    '1011111'
]

base_48_op2 = [
    '0001',
    '0010',
    '0011',
    '0100',
    '0101',
    '0110',
    '0111',
    '1000',
    '1001',
    '1010',
    '1011',
    '1100',
    '1101',
    '1110',
    '1111'
]

illegal_second = [
    'mv', 'nop', 'li', 'lui'
]

ignore = [
    'auipc', 'mv', 'nop',
    'addi4spn', 'c.addi4spn', 'addi4n', 'c.addi4n',
    'addi16sp', 'c.addi16sp', 'addi16', 'c.addi16',
    'beqz', 'bnez', 'blez', 'bgez', 'bltz', 'bgtz', 'bltu',
    'bgt', 'ble', 'blt', 'bge', 'bgtu', 'bleu', 'beq', 'bne', 'bgeu',
    'j', 'jal', 'jr', 'jalr', 'ret', 'call', 
    'tail', 'fence', 'mulh', 'mulhu', 'mulw',
    'k.lli',
    'k.lmiarn'
]

OPERATORS = {
    'add':  '+',
    'addi': '+',
    
    'sub':  '-',
    'subi': '-',
     
    'and': '&', 
    'andi': '&',
    
    'or': '|',
    'ori': '|',
    
    'xor': '^',
    'xori': '^',
    
    'srl': '>>',
    'srli': '>>',
    'sra': '>>',
    'srai': '>>',
    
    'sll': '<<',
    'slli': '<<',
    
    'mul': '*',
    
    'div': '/',
    'divu': '/',
    
    'rem': '%',
    'remu': '%',
    
    'slt': '<',
    'slti': '<',
    'sltu': '<',
    'sltiu': '<',
}

class BitWitdth(Enum):
    COMPRESSED = 16
    FULL = 32
    EXTENDED = 48

regs_util: register.Regs = register.Regs()

class Format:
    length_selecton_bits = {
        BitWitdth.COMPRESSED: 0,
        BitWitdth.FULL: 2,
        BitWitdth.EXTENDED: 6
    }
    length_selecton_exclude = {
        BitWitdth.COMPRESSED: 1,
        BitWitdth.FULL: 1,
        BitWitdth.EXTENDED: 0
    }

    width: BitWitdth = BitWitdth.FULL
    op_len: int = 0
    imm_widths: list[int] = 0

    
    def __init__(self, width: BitWitdth, opcode_len: int, imm_widths: list[int]):
        '''
        width: the total bit with of the instruction
        opcode_len: the lenght on of the opcode
        imm_widths: the width of the immediate
        '''
        assert width.value - self.length_selecton_bits[width] > opcode_len
        self.width = width
        self.op_len = opcode_len
        self.imm_widths = imm_widths

    def get_available_bits(self) -> int:
        return self.width.value - self.op_len - self.length_selecton_bits[self.width] - sum(self.imm_widths)
    
    def get_available_insts(self) -> int:
        return 2**self.op_len - self.length_selecton_exclude[self.width]
    
    def get_max_regs_codeable(self, fun_bits: int=0, compressed_reg: bool=False) -> int:
        bits_for_sel = self.get_available_bits() - fun_bits
        reg_bits = regs_util.get_width(compressed_reg)
        return int(bits_for_sel/reg_bits)

    def get_remainig_bits(self, fun_bits: int=0, reg_count: int=0, compressed_reg: int=False) -> int:
        bits_for_sel = self.get_available_bits() - fun_bits
        reg_bits = regs_util.get_width(compressed_reg) * reg_count
        remaining_bits = bits_for_sel - reg_bits
        assert int(remaining_bits) == remaining_bits
        return int(remaining_bits)


class InstFusion:
    insts: list[instruction_model.Instruction] = []
    template: list[str] = []
    t_in_reg: int = 0
    t_out_reg: int = 0

    in_regs: list[register.Reg] = []
    out_regs: list[register.Reg] = []
    imms: list[immediate.Imm] = []

    format: Format = None
    connected: bool = False

    def __init__(self, format):
        self.insts = []
        self.format = format
        self.template = []
        self.t_in_reg =  0
        self.t_out_reg = 0
        self.in_regs = []
        self.out_regs = []
        self.connected =  False
        
    def __str__(self) -> str:
        # for inst in self.insts:
        #     print(inst)
        result = str(self.format.width.value) + '.'
        for t in self.template:
            result += t + '_'
        result += '(in: ' + str(len(self.in_regs)) + ')_'
        result += '(out: ' + str(len(self.out_regs)) + ')_'
        result += '(imms: ' + str(len(self.format.imm_widths)) + ')'

        return result
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __eq__(self, other) -> bool:
        if isinstance(other, InstFusion):
            return ((self.template == other.template) and (self.t_in_reg == other.t_in_reg) and (self.t_out_reg == other.t_out_reg) and (self.format.imm_widths == other.format.imm_widths))
        else:
            return False
    def __ne__(self, other):
        return (not self.__eq__(other))
    def __hash__(self):
        return hash(tuple(self.template)) + hash(self.t_in_reg) + hash(self.t_out_reg) + hash(len(self.format.imm_widths))

    def get_regs_coded(self) -> list[register.Reg]:
        return self.t_in_reg + self.t_out_reg
    
    def get_name(self) -> str:
        return '_'.join(self.template)
    
    def print_params(self) -> str:
        result: str = ''
        in_count = len(self.in_regs) 
        out_count = len(self.out_regs)
        assert out_count < 2 and out_count + in_count > 0
        
        if out_count == 1:
            result += '{name(rd)}'
        if in_count > 0:
            result += ', '
            for i in range(in_count-1):
                result += '{name(rs' + str(i+1) + ')}, '

            result += '{name(rs' + str(in_count) + ')}'
        return result
    
    def print_encoding(self, index: int, op_len: int) -> str:
        bits_encoded = 0
        
        if self.format.width == BitWitdth.FULL:  
            ops = base_32_opcodes # + reserved_32_opcodes
            base_opcode_index = index % len(ops)
            base_opcode = ops[base_opcode_index]
            op_index = int(index / len(ops))
            op = "{0:02b}".format(op_index)
            
            encoding: str = ' :: ' + str(op_len) + '\'b' + str(op[0:(op_len-len(base_opcode)+1)] + base_opcode)
        elif self.format.width == BitWitdth.EXTENDED:
            custom_opcode_cnt = len(base_48_op2)
            ops = base_48_op2
            op_index = int(index / len(ops))
            op = "{0:02b}".format(op_index)
            
            encoding: str = ' :: ' + str(op_len) + '\'b' + str(op[0:(op_len-len(base_48_opcodes[0])+1)] + base_48_opcodes[0])
            
            bits_encoded += len(ops[0])
        else:
            assert(False)
        
        
        bits_encoded += op_len
        
        if len(self.out_regs) == 1:
            encoding = 'rd[4:0]' + encoding
            bits_encoded += 5
            
        
        in_count = len(self.in_regs) 
        if in_count > 0:
            for i in range(in_count-1):
                encoding = 'rs' + str(i+1) + '[4:0] :: ' + encoding
                bits_encoded += 5

            encoding = 'rs' + str(in_count) + '[4:0] :: ' + encoding
            bits_encoded += 5
        
        if len(self.format.imm_widths) > 0:
            imm_index = 1
            for imm_bits in self.format.imm_widths[:len(self.format.imm_widths)-1]:
                i_val = 'imm'
                if imm_index > 1:
                    i_val += str(imm_index)
                encoding = i_val + '[' + str(imm_bits-1) + ':0] :: ' + encoding
                bits_encoded += imm_bits
                imm_index += 1
                
            imm_bits = self.format.imm_widths[-1]
            if bits_encoded + imm_bits < self.format.width.value or bits_encoded + imm_bits > self.format.width.value:
                imm_bits = self.format.width.value - bits_encoded
            i_val = 'imm'
            if imm_index > 1:
                i_val += str(imm_index)
            encoding = i_val + '[' + str(imm_bits-1) + ':0] :: ' + encoding
            bits_encoded += imm_bits
            
        if bits_encoded < self.format.width.value:
            free_space = self.format.width.value - bits_encoded
            encoding = str(free_space) + '\'b' + str('0'*free_space) + ' :: ' + encoding
            bits_encoded += free_space
        
        if self.format.width == BitWitdth.EXTENDED:
            base_opcode_index = index % len(ops)
            base_opcode = ops[base_opcode_index]
            encoding = base_opcode + ' :: ' + encoding
            
        assert bits_encoded == self.format.width.value
        return encoding
    
    def get_operator(self, mnemonic: str) -> str:
        if mnemonic in OPERATORS:
            return OPERATORS[mnemonic]
        return 'UNKNOWN'
    
    def get_inst_behavior(self, inst: instruction_model.Instruction) -> list[str]:
        # print("Generating behavior for instruction:", inst)
        inst_behav = [inst]
        
        params = inst.get_params()
        base_mnemonic = inst.get_base_mnemonic()
    
        if base_mnemonic == 'lui' or base_mnemonic == 'li' or base_mnemonic == 'auipc':
            inst_behav += ['imm']
        elif base_mnemonic == 'mv':
            assert len(params) == 1
            inst_behav += [str(params[0]), '']
        else:
            if inst.has_imm():
                assert len(params) == 1
                inst_behav += [str(params[0]), self.get_operator(base_mnemonic), str(inst.get_imm())]
            else:
                assert len(params) == 2
                inst_behav += [str(params[0]), self.get_operator(base_mnemonic), str(params[1]), '']
        
        return inst_behav
    
    def get_imm(self, inst: instruction_model.Instruction, i_num: int) -> str:
        i_val = 'imm'
        if i_num > 1:
            i_val += str(i_num)
        imm = '(signed)' + i_val
        bm = inst.get_base_mnemonic()
        if bm == 'andi' or bm == 'ori' or bm == 'xori' or bm == 'sltiu':
            imm = '(unsigned<XLEN>)((signed)' + i_val + ')'
        return imm
        
    
    def behav_to_str(self, inst: instruction_model.Instruction, be: list[str], p_num: int, i_num: int):
        result = ''
        
        base_mnemonic = inst.get_base_mnemonic()
        if len(be) == 1:
            tmp = ''
            i_val = 'imm'
            if i_num > 1:
                i_val += str(i_num)
            if base_mnemonic == 'lui':
                tmp = '(unsigned<XLEN>) ((signed) ' + i_val + ')'
            elif base_mnemonic == 'li':
                tmp = '(signed)' + i_val
            elif base_mnemonic == 'auipc':
                tmp = '(PC + (signed)' + i_val + ')'
                
            result = '(' + tmp + ')'
            i_num -= 1
            
        if len(be) == 2:
            result = '(X[rs' + str(p_num) + '])'
        
        if len(be) == 3:
            result = ''
            base_mnemonic = inst.get_base_mnemonic()
            is_slti_u = base_mnemonic == 'slti' or base_mnemonic == 'sltiu'
            if is_slti_u:
                result += '('
            result += '(X[rs' + str(p_num) + '] ' + be[1] + ' ' + str(self.get_imm(inst, i_num)) 
            if is_slti_u:
                result += ') ? 1 : 0'                    
            result += ')'
            p_num -= 1
            i_num -= 1
        
        if len(be) == 4:
            result = ''
            is_sltu = inst.get_base_mnemonic() == 'sltu'
            if is_sltu:
                result += '('
            result += '(X[rs' + str(p_num-1) + '] ' + be[1] + ' X[rs' + str(p_num) + '])'
            if is_sltu:
                result += ' ? 1 : 0)'
            p_num -= 2
        
        assert p_num >= 0
        return (result, p_num, i_num)
            
    def get_asm(self):
        asm =  '"arise' + str(self.format.width.value) + '.' + self.get_name() + '", "' + self.print_params()
        if len(self.format.imm_widths) > 0:
            for imm_i in reversed(range(1, len(self.format.imm_widths)+1)):
                i_val = 'imm'
                if imm_i > 1:
                    i_val += str(imm_i)
                asm += ', {' + i_val + '}'
            
        asm += '"'
        return asm
            
    def print_behavior(self) -> str:
        behavs = []
        p_num = len(self.in_regs)
        i_num = len(self.format.imm_widths)
        for inst in self.insts:
            behavs += [self.get_inst_behavior(inst)]
        
        behavior: str = ''
        
        inst: instruction_model.Instruction = behavs[0][0]
        be = behavs[0][1:]
        out = inst.get_dest()
        behavior, p_num, i_num = self.behav_to_str(inst, be, p_num, i_num)
        for tmp in behavs[1:]:
            inst = tmp[0]
            be = tmp[1:]
            
            if len(be) == 3:
                behavior = '(' + behavior + ' ' + be[1] + ' ' + str(self.get_imm(inst, i_num)) + ')'
                i_num -= 1
                
            elif len(be) == 4:
                param = 'X[rs' + str(p_num) + ']'
                if p_num <= 0:
                    param = 'X[rd]'
                if be[0] == out:
                    behavior = '(' + behavior + ' ' + be[1] + ' ' + param + ')'
                else:
                    behavior = '(' + param + ' ' + be[1] + ' ' + behavior + ')'
                
                if inst.get_base_mnemonic() == 'sltu':
                    behavior = '(' + behavior + ' ? 1 : 0)'
                p_num -= 1
            else:
                print(self)
                print(be)
                assert False
            out = inst.get_dest()
            
        behavior = 'if ((rd) != 0) X[rd] = ' + behavior
        
        return behavior
    
    def to_cdsl(self, index: int, op_len: int) -> str:
        # Only FULL is currently supported
        return '    ' + self.get_name().upper() + ''' {
      encoding: ''' + self.print_encoding(index, op_len) + ''';
      assembly: {''' + self.get_asm() + '''};
      behavior: {
        ''' + self.print_behavior() + ''';
      }
    }

'''


def get_diff(in1: list, in2: list) -> list:
    return list(set(in1).difference(set(in2)))


def get_common(in1: list, in2: list) -> list:
    return list(set(in1).intersection(set(in2)))


def consumes_out(out_regs: list[register.Reg], inst: instruction_model.Instruction) -> bool:
    return len(get_common(inst.get_params(), out_regs)) > 0


def is_extendable(pat: InstFusion, inst: instruction_model.Instruction, fun_bits: int, one_imm: bool) -> bool:
    is_compressed = pat.format.width == BitWitdth.COMPRESSED
    inst_in: list[register.Reg] = inst.get_params().copy()
    has_dest: bool = inst.has_dest()
    regs_coded: int = pat.get_regs_coded()
    captured_out: list[register.Reg] = get_common(inst_in, pat.out_regs.copy())
    new_in: list[register.Reg] = get_diff(inst_in, captured_out)
    
    if inst.has_imm() and len(pat.imms) > 0 and one_imm:
        return False
    
    if len(captured_out) == 0 or not has_dest: 
        return False
    
    new_regs: int = regs_coded + len(new_in) - len(captured_out)
    if has_dest:
        new_regs += 1
    is_compressed_reg: bool = is_compressed
    

    remaining_bits = pat.format.get_remainig_bits(fun_bits, new_regs, is_compressed_reg)
    
    if inst.has_imm():
        remaining_bits -= inst.get_imm().get_needed_bits()
    
    return remaining_bits >= 0


def extend(pat: InstFusion, inst: instruction_model.Instruction, first: bool = False):
    inst_mnemonic = inst.get_base_mnemonic()
    inst_out: register.Reg = inst.get_dest()
    inst_in: list[register.Reg] = inst.get_params().copy()
    has_dest: bool = inst.has_dest()
    
    captured_out: list[register.Reg] = get_common(inst_in, pat.out_regs)
    assert (len(pat.template) == 0) or(len(captured_out) == 1 and len(pat.out_regs) == 1 and captured_out[0] == pat.out_regs[0])
    
    new_in: list[register.Reg] = get_diff(inst_in, captured_out)
    pat.template += [inst_mnemonic]
    
    if first:
        pat.in_regs = inst_in
    else:
        pat.in_regs += new_in
        
    pat.out_regs = [inst_out]
    
    pat.t_in_reg = len(pat.in_regs)
    pat.t_out_reg = len(pat.out_regs)
    
    pat.connected = len(inst_in) > len(new_in)
    
    pat.insts += [inst]
    
    if inst.has_imm():
        imm = inst.get_imm()
        pat.imms.append(imm)
        pat.format.imm_widths += [max(1, imm.get_needed_bits())]


def greedy_inst_gen(instructions: list[instruction_model.Instruction], bit_width: BitWitdth, op_len: int, ignore_mem: bool = True, one_imm: bool = True) -> set[InstFusion]:
    '''
    ToDo: take care of compressed regs for gen and pattern
    '''
    new_insts: list[InstFusion] = []
    fun_bits = 0
    prev_pat: InstFusion = None
    out_regs = []
    create_new = False
    
    # print(len(instructions))
    
    for inst in instructions:
        mnem = inst.get_base_mnemonic() 
              
        if inst.get_base_mnemonic() in instruction_model.branch:
            create_new = True
        
        if create_new or prev_pat == None:
            format: Format = Format(bit_width, op_len, [])
            prev_pat = InstFusion(format)
            out_regs = []
            create_new = False
        
        first = len(prev_pat.insts) == 0
        is_ignored = ignore_mem and (mnem in instruction_model.load or mnem in instruction_model.store) 
        is_ignored = is_ignored or mnem in ignore
        is_ignored = is_ignored or mnem[0] == 'f'
        forbidden_second = False
        if len(prev_pat.insts) > 0:
            forbidden_second = mnem in illegal_second
            prev_mnem = prev_pat.insts[0].get_base_mnemonic()
            forbidden_second = forbidden_second or ((prev_mnem == 'li' or prev_mnem == 'lui') and (inst.has_imm() or (mnem != 'mul' and mnem != 'div')))
        extendable = first or is_extendable(prev_pat, inst, fun_bits, one_imm)
        if not forbidden_second and not is_ignored and extendable:
            # Pattern is extendable to match inst
            extend(prev_pat, inst, first=first) 
            out_regs = [inst.get_dest()]
        else:
            create_new = not extendable or consumes_out(out_regs, inst)
            # Cannot extend pat further when a out gets consumed
            
        if create_new and prev_pat != None:
            if len(prev_pat.format.imm_widths) > 0:
                prev_pat.format.imm_widths[-1] += prev_pat.format.get_remainig_bits(fun_bits, prev_pat.get_regs_coded(), prev_pat.format.width == BitWitdth.COMPRESSED)
                prev_pat.format.imm_widths[-1] = max(1, prev_pat.format.imm_widths[-1])
                
            if len(prev_pat.insts) > 0:
                new_insts += [prev_pat]

    return set(new_insts)

def merge_patterns(pats: set[InstFusion]) -> set[InstFusion]:
    result = pats.copy()
    for pat1 in pats:
        for pat2 in pats:
            if pat2 in result and pat1 != pat2:
                remove = len(pat1.in_regs) == len(pat2.in_regs) \
                    and len(pat1.out_regs) == len(pat2.out_regs) \
                    and pat1.template == pat2.template \
                    and len(pat1.format.imm_widths) == len(pat2.format.imm_widths) \
                    and pat1.format.imm_widths[-1] > pat2.format.imm_widths[-1]
                remove = remove or pat1.template == pat2.template
                if remove:
                    result.remove(pat2)
            
    return result


def match_pattern(insts: list[instruction_model.Instruction], pat: InstFusion, index: int) -> tuple[bool, list[instruction_model.Instruction], int]:
    pat_match = True
    n = len(pat.template)
    i = index
    matched = []
    matched_len = 0
    total_imm = 0
    out_regs = []
    insts_len = len(insts)
    
    
    while pat_match and matched_len < n and insts_len > i:
        candidate: instruction_model.Instruction = insts[i]
        
        mnem_match = candidate.get_base_mnemonic() == pat.template[matched_len]
        
        if mnem_match:
            if candidate.has_imm():
                total_imm += candidate.get_imm().get_needed_bits()
            out_regs += [candidate.get_dest()]
            matched += [candidate]
            matched_len += 1
        else:
            if consumes_out(out_regs, candidate):
                pat_match = False
            if candidate.get_base_mnemonic() in instruction_model.branch:
                pat_match = False
                
        i += 1
    return pat_match, matched, total_imm


def get_dynamic_count(matched, inst_cnt):
    contains = True
    cnt_sum = 0
    for inst in matched:
        opcode = inst.get_address()
        if opcode in inst_cnt:
            cnt_sum += inst_cnt[opcode][1]
            contains = False
    
    # if not contains:
    #     print("INFO: Sequence never executed:")
    #     for mi in matched:
    #         print('    ', mi)
    return cnt_sum / len(matched)


def get_size_improvement(pat: InstFusion, insts: list[instruction_model.Instruction], index: int, inst_cnt) -> int:
    pat_match, matched, total_imm = match_pattern(insts, pat, index)
    imm_match = total_imm <= sum(pat.format.imm_widths)
    if pat_match and imm_match:
        improvement = evaluator.get_byte_count(matched) - int(pat.format.width.value/8)
        if len(inst_cnt) > 0:
            cnt_sum = get_dynamic_count(matched, inst_cnt)
            if cnt_sum > 0:
                improvement *= cnt_sum
        if improvement >= 0:
            return improvement
    return 0
       
       
def get_inst_count_reduction(pat: InstFusion, insts: list[instruction_model.Instruction], index: int, inst_cnt) -> int:
    pat_match, matched, total_imm = match_pattern(insts, pat, index)
    imm_match = total_imm <= sum(pat.format.imm_widths)
    if pat_match and imm_match:
        improvement = len(pat.insts) - 1
        if len(inst_cnt) > 0:
            cnt_sum = get_dynamic_count(matched, inst_cnt)
            if cnt_sum > 0:
                improvement *= cnt_sum
        if improvement >= 0:
            return improvement
    return 0
       

def select_insts(insts: list[instruction_model.Instruction], proposed: set[InstFusion], inst_cnt, metric, width) -> typing.Dict[InstFusion, int]:
    inst_len = len(insts)
    op_len = BASE_OP_LEN + CUST_OP_LEN
    pat_sel_count = get_available_inst_count(op_len, width)
    pat_eval: map[InstFusion, int] = {
        pat: sum([
            metric(pat, insts, index, inst_cnt)
            for index in range(inst_len)
            if pat.template[0] == insts[index].get_base_mnemonic() and inst_len >= index + len(pat.template) and len(pat.template) > 1
        ])
        for pat in proposed
    }
    
    return evaluator.sort_dict(pat_eval, pat_sel_count)
    
    
def get_available_inst_count(op_len, width):
    if width == BitWitdth.FULL:  
        custom_opcode_cnt = len(base_32_opcodes) # + len(reserved_32_opcodes)
    elif width == BitWitdth.EXTENDED:
        custom_opcode_cnt = len(base_48_op2)
    else:
        assert(False)
    return custom_opcode_cnt * (2**(op_len-7))  
     
            
def write_cdsl(path: str, name: str, file_name: str, new_insts: list[InstFusion], width: BitWitdth, inst_cnt: int, op_len: int):
    ise_name = 'ARISE' # + name.replace('-', '').upper()
    file_content: str = '''import "../../common/cdsl/rv_base/RV32I.core_desc"

InstructionSet ''' + ise_name + ''' extends RV32I {
  instructions {
'''
    i = 0
    for new_inst in new_insts:
        if len(new_inst.insts) > 1 and i < inst_cnt:
            file_content += new_inst.to_cdsl(i, op_len)
            i += 1
    file_content += '''  }
}''' 
    # Write file
    file_path = os.path.join(path, file_name)
    with open(file_path, 'w') as file:
        file.write(file_content)


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
    exe_time = args.time
    print_results = args.results
    csv = args.csv
    
    total_base = 0
    total_new = 0
    
    ign = {
        'mnemonic': instruction_model.load + instruction_model.store + ignore,
        'opcode': 0x80000000
    }
    
    # print('Start parsing')
    if debug:
        print('Base Path: ', path)
        
    for file in args.files:
        if debug or True:
            print('File to analyze: ', file)

        fqpn = '{}/{}'.format(str(path), str(file))
        
        start = perf_counter_ns()
        instructions = parse_utils.parse_file(
            fqpn.replace('_trace_etiss.txt', '.etiss_asm'),
            static.parse_line, 
            ign
        )
        print("Instructions parsed:", len(instructions))
        if exe_time:
            stop = perf_counter_ns()
            elapsed_micro = int(round((stop - start)/NANO_TO_MICOR, 0))
            if csv:
                print(file.replace('.etiss_asm', ''), len(instructions), elapsed_micro, end=',', sep=',')
            else:
                print('Target:', file)
                print('Static instructions to use:', len(instructions))
                print('Static parse time: ', elapsed_micro, 'micros')
        
        addr_instruction_map: map[int, instruction_model.Instruction] = {
            inst.get_address(): inst
            for inst in instructions
        }
        
        if debug:
            for inst in instructions:
                print(inst)
                assert inst.get_address() in addr_instruction_map
            print(len(instructions), '==', len(addr_instruction_map.keys()))
        
        inst_cnt = {}
        
        if static_file and dynamic_file:
            print('Error: static and dynamic mix currently not supported')
            assert False 
        elif dynamic_file:
            if '.etiss_asm' in fqpn:
                fqpn = fqpn.replace('.etiss_asm', '_trace.txt')  
            if debug:
                print('File to analyze: ', fqpn)   
            
            start = perf_counter_ns()
            # dynamic.get_spike_addr 
            inst_cnt = parse_utils.parse_address_cnt(
                fqpn,
                addr_instruction_map, 
                dynamic.get_etiss_addr
            )
            
            if exe_time:
                stop = perf_counter_ns()
                elapsed_micro = int(round((stop - start)/NANO_TO_MICOR, 0))
                dynamic_inst_cnt = sum([inst_cnt[op][1] for op in inst_cnt])
                if csv:
                    print(dynamic_inst_cnt, elapsed_micro, end=',', sep=',')
                else:
                    print('Dynamic instructions to use:', dynamic_inst_cnt)
                    print('Dynamic parse time: ', elapsed_micro, 'micros')
            if debug:
                for opcode in inst_cnt:
                    inst, cnt = inst_cnt[opcode]
                    print(cnt, ' : ', inst)
        
        name = file.split('.')[0]
        ext_file_name: str = '_' + name + '_'
        if static_file and dynamic_file:
            assert False
        elif static_file:
            ext_file_name += 'static'
        elif dynamic_file:
            ext_file_name += 'dynamic' 
        else:
            assert False
        if size and count:
            assert False
        elif size:
            ext_file_name += '_size'
        elif count:
            ext_file_name += '_count'
        else:
            assert False
        ext_file_name += '.core_desc'
        if len(instructions) > 0:
            opti_base = 1
            if static_file:
                if size and count:
                    print('Error: optimization mix currently not implemented')
                elif size:
                    opti_base = evaluator.get_byte_count(instructions)
                elif count:
                    opti_base = len(instructions)
                else:
                    print('ERROR: eighter size or count should be set')
            elif dynamic_file:
                if size and count:
                    print('Error: optimization mix currently not implemented')
                elif size:
                    opti_base = evaluator.get_cnt_byte_count(inst_cnt)
                elif count:
                    opti_base = sum(pair[1] for pair in [*map(inst_cnt.get, inst_cnt.keys())])
                else:
                    print('ERROR: eighter size or count should be set')
            else:
                assert False
                    
            for width in [BitWitdth.FULL, BitWitdth.EXTENDED]:
                file_name = 'ARISE' + str(width.value) + ext_file_name
                op_len = BASE_OP_LEN + CUST_OP_LEN
                pat_sel_count = get_available_inst_count(op_len, width)
                # print('Start Generating')
                # print(width)
                
                start = perf_counter_ns()   
                new_insts: list[InstFusion] = greedy_inst_gen(instructions, width, op_len, ignore_mem=True, one_imm=True)
                if exe_time:
                    stop = perf_counter_ns()
                    elapsed_micro = int(round((stop - start)/NANO_TO_MICOR, 0))
                    if csv:
                        print(elapsed_micro, end=',', sep='')
                    else:
                        print('Generation elapsed time: ', elapsed_micro, 'micros')
                
                
                new_insts.union(greedy_inst_gen(instructions, width, op_len, ignore_mem=True, one_imm=False))
                #print('Start Merging')
                
                start = perf_counter_ns() 
                new_insts = merge_patterns(new_insts)
                if exe_time:
                    stop = perf_counter_ns()
                    elapsed_micro = int(round((stop - start)/NANO_TO_MICOR, 0))
                    if csv:
                        print(elapsed_micro, end=',', sep='')
                    else:
                        print('Merge elapsed time: ', elapsed_micro, 'micros')
                
                # print('Start Selecting')
                
                if size and count:
                    print('Error: optimization mix currently not implemented')
                    assert False
                elif size:
                    metric = get_size_improvement
                elif count:
                    metric = get_inst_count_reduction
                
                
                start = perf_counter_ns()   
                frequencies = select_insts(instructions, new_insts, inst_cnt, metric, width)
                if exe_time:
                    stop = perf_counter_ns()
                    elapsed_micro = int(round((stop - start)/NANO_TO_MICOR, 0))
                    if csv:
                        print(elapsed_micro, end='', sep='')
                    else:
                        print('Selection elapsed time: ', elapsed_micro, 'micros')
                    print()
                
                selected: list[InstFusion] = []
                total_improvement = 0
                i = 0
                for inst, improvement in frequencies:
                    if len(inst.template) > 1 and i < pat_sel_count:
                        selected += [inst]
                        if print_results:
                            total_improvement += improvement
                            total_base += opti_base
                            total_new += total_improvement
                            factor = evaluator.rel(improvement, opti_base)
                            print(i, ':', inst, ': ', improvement, '(', factor,'%)')
                        i += 1
                if print_results:  
                    met = 'byte'
                    if count:
                        met = 'Instructions'
                    print('Total Improvement: ', total_improvement, met, '(', evaluator.rel(total_improvement, opti_base),'%)')
                    print()
                if not exe_time:
                    write_cdsl(path, name, file_name, selected, width, pat_sel_count, op_len)    
    if print_results:
        print()
        ty = 'static'
        if dynamic_file:
            ty = 'dynamic'
        met = 'size'
        if count:
            met = 'count'
        print('Overall average', ty, met, 'improvement:', evaluator.rel(total_new, total_base), '%')
            

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate new Instructions.')
    parser.add_argument('files', metavar='F', type=str, nargs='+', help='files as basis for instruction generation')
    parser.add_argument('--static', type=bool, default=False, help='Generate based on static insts')
    parser.add_argument('--dynamic', type=bool, default=False, help='Generate based on dynamic insts')
    parser.add_argument('--size', type=bool, default=False, help='Generate based on size optimization')
    parser.add_argument('--count', type=bool, default=False, help='Generate based on instr count optimization')
    parser.add_argument('--time', type=bool, default=False, help='Measure exe time')
    parser.add_argument('--csv', type=bool, default=False, help='Print time in CSV')
    parser.add_argument('--results', type=bool, default=False, help='Print results')
    parser.add_argument('--path', type=str, help='base path for the files') 
    parser.add_argument('--debug', type=bool, help='print debug messages')

    main(parser.parse_args())

