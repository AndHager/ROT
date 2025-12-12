import math
from bitstring import Array
from enum import Enum
from typing import Tuple

class SavedBy(Enum):
    NotSaved = 'N'
    CALLER = 'R'
    CALLEE = 'E'


class Reg:
    names: list[str] = []
    saved_by: SavedBy = None

    def __init__(self, names: list[str], saved_by: SavedBy):
        self.names = names
        self.saved_by = saved_by
        
    def __str__(self) -> str:
        return str(self.names[0])

    def equals(self, other) -> bool:
        if type(self) != type(other):
            return False
        if type (other) == str:
            return other in self.names
        return self.names == other.names


class Regs:
    all: list[Reg] = []
    reduced_regs: list[Reg] = []
    fregs: list[Reg] = []

    # encoded in 5 bits
    def __init__(self):
        self.all = [
            Reg(['x0', 'x0'], SavedBy.NotSaved), # hardwired zero
            Reg(['ra', 'x1'], SavedBy.CALLER), # return address
            Reg(['sp', 'x2'], SavedBy.CALLEE), # stack pointer
            Reg(['gp', 'x3'], SavedBy.NotSaved), # global pointer
            Reg(['tp', 'x4'], SavedBy.NotSaved), # thread pointer
            Reg(['t0', 'x5'], SavedBy.CALLER), # tmp  0
            Reg(['t1', 'x6'], SavedBy.CALLER), # tmp  1
            Reg(['t2', 'x7'], SavedBy.CALLER), # tmp  2
            Reg(['s0', 'fp', 'x8'], SavedBy.CALLEE), # frame pointer / saved  0
            Reg(['s1', 'x9'], SavedBy.CALLEE), # saved  1
            Reg(['a0', 'x10'], SavedBy.CALLER), # ret val 0 / arg 0
            Reg(['a1', 'x11'], SavedBy.CALLER), # ret val 1 / arg 1
            Reg(['a2', 'x12'], SavedBy.CALLER), # arg 2
            Reg(['a3', 'x13'], SavedBy.CALLER), # arg 3
            Reg(['a4', 'x14'], SavedBy.CALLER), # arg 4
            Reg(['a5', 'x15'], SavedBy.CALLER), # arg 5
            Reg(['a6', 'x16'], SavedBy.CALLER), # arg 6
            Reg(['a7', 'x17'], SavedBy.CALLER), # arg 7
            Reg(['s2', 'x18'], SavedBy.CALLEE), # saved  2
            Reg(['s3', 'x19'], SavedBy.CALLEE), # saved  3
            Reg(['s4', 'x20'], SavedBy.CALLEE), # saved  4
            Reg(['s5', 'x21'], SavedBy.CALLEE), # saved  5
            Reg(['s6', 'x22'], SavedBy.CALLEE), # saved  6
            Reg(['s7', 'x23'], SavedBy.CALLEE), # saved  7
            Reg(['s8', 'x24'], SavedBy.CALLEE), # saved  8
            Reg(['s9', 'x25'], SavedBy.CALLEE), # saved  9
            Reg(['s10', 'x26'], SavedBy.CALLEE), # saved  10
            Reg(['s11', 'x27'], SavedBy.CALLEE), # saved  11
            Reg(['t3', 'x28'], SavedBy.CALLER), # tmp 3
            Reg(['t4', 'x29'], SavedBy.CALLER), # tmp 4
            Reg(['t5', 'x30'], SavedBy.CALLER), # tmp 5
            Reg(['t6', 'x31'], SavedBy.CALLER) # tmp 6
        ]
        
        self.fregs = [
            Reg(['zero'], SavedBy.NotSaved), # FP zero
            Reg(['ft0', 'f0'], SavedBy.CALLER), # FP temporaries
            Reg(['ft1', 'f1'], SavedBy.CALLER), # FP temporaries
            Reg(['ft2', 'f2'], SavedBy.CALLER), # FP temporaries
            Reg(['ft3', 'f3'], SavedBy.CALLER), # FP temporaries
            Reg(['ft4', 'f4'], SavedBy.CALLER), # FP temporaries
            Reg(['ft5', 'f5'], SavedBy.CALLER), # FP temporaries
            Reg(['ft6', 'f6'], SavedBy.CALLER), # FP temporaries
            Reg(['ft7', 'f7'], SavedBy.CALLER), # FP temporaries
            Reg(['fs0', 'f8'], SavedBy.CALLEE), # FP saved regs
            Reg(['fs1', 'f9'], SavedBy.CALLEE), # FP saved regs
            Reg(['fa0', 'f10'], SavedBy.CALLER), # FP arguments / return values
            Reg(['fa1', 'f11'], SavedBy.CALLER), # FP arguments / return values
            Reg(['fa2', 'f12'], SavedBy.CALLER), # FP arguments
            Reg(['fa3', 'f13'], SavedBy.CALLER), # FP arguments
            Reg(['fa4', 'f14'], SavedBy.CALLER), # FP arguments
            Reg(['fa5', 'f15'], SavedBy.CALLER), # FP arguments
            Reg(['fa6', 'f16'], SavedBy.CALLER), # FP arguments
            Reg(['fa7', 'f17'], SavedBy.CALLER), # FP arguments
            Reg(['fs2', 'f18'], SavedBy.CALLEE), # FP saved registers
            Reg(['fs3', 'f19'], SavedBy.CALLEE), # FP saved registers
            Reg(['fs4', 'f20'], SavedBy.CALLEE), # FP saved registers
            Reg(['fs5', 'f21'], SavedBy.CALLEE), # FP saved registers
            Reg(['fs6', 'f22'], SavedBy.CALLEE), # FP saved registers
            Reg(['fs7', 'f23'], SavedBy.CALLEE), # FP saved registers
            Reg(['fs8', 'f24'], SavedBy.CALLEE), # FP saved registers
            Reg(['fs9', 'f25'], SavedBy.CALLEE), # FP saved registers
            Reg(['fs10', 'f26'], SavedBy.CALLEE), # FP saved registers 
            Reg(['fs11', 'f27'], SavedBy.CALLEE), # FP saved registers 
            Reg(['ft8', 'f28'], SavedBy.CALLER), # FP temporaries
            Reg(['ft9', 'f29'], SavedBy.CALLER), # FP temporaries
            Reg(['ft10', 'f30'], SavedBy.CALLER), # FP temporaries 
            Reg(['ft11', 'f31'], SavedBy.CALLER) # FP temporaries
        ]

        # encoded in 3 bits
        self.reduced_regs = self.all[8:16]
        assert len(self.all) == 32
        assert len(self.reduced_regs) == 8

    def get_reg(self, name: str, compressed_reg:bool=False) -> Tuple[bool, Reg]:
        regs = self.all + self.fregs
        if compressed_reg:
            regs = self.reduced_regs
        for reg in regs:
            if name in reg.names:
                return (True, reg)
        return (False, None)

    def get_all(self) -> list[Reg]:
        return self.all
    
    def get_width(self, compressed:bool=False) -> int:
        regs = self.all
        if compressed:
            regs = self.reduced_regs
        width = math.log(len(regs), 2)
        assert int(width) == width
        return int(width)
    
    def get_reduced(self) -> list[Reg]:
        return self.reduced_regs

    def get_reg_only(self, name:str, compressed_reg:bool=False) -> Reg:
        return self.get_reg(name, compressed_reg)[0]
    
    def get_coding(self, name, compressed_reg=False) -> Array:
        index, _ = self.get_index_reg(name)
        assert index >= 0
        format = f'uint{self.get_width(compressed_reg)}'
        return Array(format, index)
