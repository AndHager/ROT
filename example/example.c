#include <stdio.h>
#include <stdint.h>


// SLLI_OR {
//     encoding: imm[7:0] :: rs2[4:0] :: rs1[4:0] :: rd[4:0] :: 9'b000101011;
//     assembly: {"arise32.slli_or", "{name(rd)}, {name(rs1)}, {name(rs2)}, {imm}"};
//     behavior: {
//       if ((rd) != 0) X[rd] = (X[rs1] | (X[rs2] << (signed)imm));
//     }
// }

int32_t slli_or_2(int32_t x, int32_t y)
{
    return x | (y << 1);
}


// int32_t slli_or(int32_t x, int32_t y)
// {
//     int32_t res;
//     // arise32.slli_or x5, x6, x7, 0x1
//     asm volatile (
//         "mv x6, %1\n\t"       // Move x into x6
//         "mv x7, %2\n\t"       // Move y into x6
//         ".insn 0x4, 0x01398a2b\n\t"  // Custom 48-bit instruction
//         "mv %0, x5"           // Store result back into res
//         : "=r"(res)           // Output operand
//         : "r"(x), "r"(y)      // Input operands
//         : "x5", "x6", "x7"          // Clobbered registers
//     );
//     return res;
// }

int main()
{
    volatile const int32_t a = 0xAA;
    volatile const int32_t b = 0x55;
    // int32_t res1 = slli_or(a, b);
    // printf("res=%x\n", res1);

    int32_t res2 = slli_or_2(a, b);
    printf("res2=%x\n", res2);
}