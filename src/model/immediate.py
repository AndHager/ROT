from typing import Tuple
from bitstring import Array
import math
import re


class Imm:
    value: int = 0

    def __init__(self, value: int):
        self.value = value
        
    def __str__(self)  -> str:
        return hex(self.value)

    def get_needed_bits(self, signed=True) -> int:
        if self.value == 0:
            return 1
        result = int(math.log(abs(self.value), 2))
        if result == 0:
            return 1
        return result

    def get_coding(self) -> Array:
        format = f'uint{self.get_needed_bits()}'
        return Array(format, self.value)


def is_hex(s):
    return re.fullmatch(r"^[0x]*[0-9a-fA-F]+$", s or "") is not None

def is_integer_num(n) -> bool:
    if isinstance(n, int):
        return True
    if isinstance(n, float):
        return n.is_integer()
    if is_hex(n):
        return True
    try:
        return float(str(n)).is_integer()
    except:
        return False


def to_int(n, base) -> int:
    return int(n)


def to_imm(val: str) -> Tuple[bool, Imm]:
    val = val.strip()
    vals = val.split('=')
    vlen = len(vals)

    if (val == '0x0'):
        return (True, Imm(0))
    
    # objdump imm representation
    if vlen == 1:
        if val[:2] == '0x' or val[:3] == '-0x':
            return (True, Imm(int(val, 16)))
        if is_integer_num(val):
            return (True, Imm(int(val)))
        
    # ETISS imm representation
    if vlen == 2 and 'imm' == vals[0] and is_integer_num(vals[1]):
        return (True, Imm(int(vals[1])))
    
    return (False, None)

