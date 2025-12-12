from model import register, immediate

store = [
    'sd', 'sw', 'sh', 
    'sb', 'sbu', 'shu',
    'fsd', 'fsd',
    'sd', 'sw', 'swsp',
    'fsw', 'fsd',
    'c.sd', 'c.sw', 'c.swsp'
    'c.fsw', 'c.fsd'
]

load = [
    'ld', 'lw', 'lh', 
    'lb', 'lbu', 'lhu',
    'fld', 'fld',
    'ld', 'lw', 'lwsp',
    'flw', 'fld',
    'c.ld', 'c.lw', 'c.lwsp'
    'c.flw', 'c.fld'
]

dup_compressed = [
    'c.addi', 'c.add',
    'c.subi', 'c.sub', 
    'c.andi', 'c.and',
    'c.or', 'c.ori',
    'c.slli',
    'c.lui',
    'c.srai',
    'c.srli',
    'c.xori', 'c.xor',
]

no_dest = store

branch = [
    'j', 'jal', 'jalr', 'jr',
    'ret', 'call', 'tail',
    'beqz', 'beq', 'bnez', 'bne',
    'blez', 'blt', 'bltz', 'bge', 'bgez',
    'bgtz', 'bgt', 'bgtu', 'bltu',
    'bleu', 'bgeu'
]

reg_util = register.Regs()

class Instruction:
    address: str = ''
    opcode: str = ''
    mnemonic: str = ''
    regs: list[register.Reg] = []
    imm: immediate.Imm = None
    branch_target = None

    def __init__(self, address: str, opcode: str, mnemonic: str):
        if len(opcode) % 2 != 0:
            opcode = '0' + opcode
        self.address = address
        self.opcode = opcode
        self.mnemonic = mnemonic
        self.regs = []

    def __str__(self) -> str:
        shift = 32
        if len(self.opcode) < 16:
            shift = 12
        result = str(self.address) + '\t' + str(self.opcode) + ((shift - len(str(self.opcode))) * ' ') + ' ' + str(self.mnemonic) + ' ' 
        param_size = len(self.regs)
        for i in range(param_size):
            result += str(self.regs[i])
            if i != param_size - 1 or self.has_imm():
                result += ', '
        if self.has_imm():
            result += str(self.imm)   
        
        return result
    
    def append_param(self, param: str):
        is_reg, reg = reg_util.get_reg(param)
        
        if self.mnemonic in branch: 
            self.branch_target = param
        if is_reg:
            self.regs.append(reg)
        else:
            is_imm, imm = immediate.to_imm(param)
            if is_imm:
                if self.imm != None:
                    raise Exception('ERROR: instruction ', str(self), ' has aleready a imm imm!')
                self.imm = imm
    
    def get_size(self) -> int:
        'retruns the instruction code size in bytes'
        assert len(self.opcode) % 2 == 0
        if len(self.opcode) < 16:
            return int(len(self.opcode)/2)
        assert len(self.opcode) % 16 == 0
        return int(len(self.opcode)/8)
    
    def get_params(self) -> list[register.Reg]:
        if self.mnemonic in no_dest:
            return self.regs
        if self.mnemonic in dup_compressed:
            return self.regs
        return self.regs[1:]
    
    def get_dest(self) -> register.Reg:
        if not self.has_dest():
            return 'no_dest'
        return self.regs[0]
    
    def has_dest(self) -> bool:
        return not (self.mnemonic in no_dest or len(self.regs) < 1)

    def has_imm(self) -> bool:
        return self.imm != None
    
    def get_address(self) -> int:
        return int(self.address, 16)

    def get_imm(self) -> immediate.Imm:
        # if not self.has_imm() or type(self.imm) != immediate.Imm:
        #     raise Exception('ERROR: instruction ', str(self), ' has no imm!')
        return self.imm
    
    def get_base_mnemonic(self) -> str:
        return str(self.mnemonic) \
            .replace('c.', '') \
            .replace('sp', '')
    
    def is_compressed(self) -> bool:
        return self.get_size() == 2
    
    def is_48_inst(self) -> bool:
        return self.get_size() == 6
    