"""
Catamount Processor Unit ALU

We are limited to 16 bits, and six operations: ADD, SUB, AND, OR, XOR, and SHFT.

ALU maintains status flags:

    - N: negative, 1000   (8)
    - Z: zero, 0100       (4)
    - C: carry out, 0010  (2)
    - V: overflow, 0001   (1)

Our ALU will set flags as appropriate on each operation (no special
instructions are needed for setting flags).

- Negative flag is set if the MSB = 1, regardless of operation.

- Zero flag is set if result is zero, regardless of operation.

- Carry flag under the following conditions:
    - If an arithmetic operation is used and a bit is carried out.
    - For similarity with ARM architecture carry is set on a SUB
      if the minuend is larger than or equal to the subtrahend (i.e.,
      no borrow occurs), e.g., with 5 - 2 = 3, 5 is the minuend, and 2
      is the subtrahend. Operands are compared as unsigned values.
    - On a left shift, the carry flag is set to the value of the last
      bit shifted out. So, for example, in four bits, `0b1001 << 1`
      would set the carry flag to 1. However, `0b1001 << 2` would set
      the carry flag to 0, because the last bit shifted out was 0.
      On a right shift, the carry flag is set to the value of the last
      bit shifted out on the right. For example, `0b1001 >> 1` would
      set carry flag to 1, and `0b1001 >> 2` would set carry flag to 0.
    - In the odd, but permitted case of shift by zero, the carry flag
      is cleared (flags are always cleared before each operation, and
      there is no bit shifted out to set it).
    - Carry flag is cleared on a bitwise operation.

- Overflow only applies to arithmetic operations (ADD and SUB); it is
  cleared on all others.

Every operation overwrites all four flags: it sets those that apply and
clears the rest. Flags persist only until the next ALU operation.

CS 2210 Computer Organization
Clayton Cafiero <cbcafier@uvm.edu>

Deirdre Kaniewski and Shade Rothkopf
"""

from constants import WORD_MASK, WORD_SIZE

N_FLAG = 0b1000
Z_FLAG = 0b0100
C_FLAG = 0b0010
V_FLAG = 0b0001


class Alu:
    def __init__(self):
        """
        Here we initialize the ALU when instantiated.
        """
        self._op = None
        self._flags = 0b0000
        # Dictionary to look up methods by operation name.
        self._ops = {
            "ADD": self._add,
            "SUB": self._sub,
            "AND": self._and,
            "OR": self._or,
            "XOR": self._xor,
            "SHFT": self._shft,
        }

    def set_op(self, op):
        """
        Public-facing setter.
        """
        if op in self._ops.keys():
            self._op = op
        else:
            raise ValueError(f"Bad op: {op}")

    def decode(self, c):
        """
        Decode control signal to determine operation.
        """
        c = c & 0b111  # ensure only three bits are used
        match c:
            case 0b000:
                self._op = "ADD"
            case 0b001:
                self._op = "SUB"
            case 0b010:
                self._op = "AND"
            case 0b011:
                self._op = "OR"
            case 0b100:
                self._op = "SHFT"
            case 0b101:
                self._op = "SUB"
            case _:
                raise ValueError("Invalid control signal")
        # Return value is for testing.
        # We don't really need return value for normal use.
        return self._op

    # The @property decorator makes a getter method accessible
    # as if it were a property or attribute. For example, we can
    # access the zero flag with `alu.zero`.

    @property
    def zero(self):
        """
        Return zero flag
        """
        # Return zero flag; do not modify this method!
        return bool(self._flags & Z_FLAG)

    @property
    def negative(self):
        """
        Return negative flag
        """
        return bool(self._flags & N_FLAG)

    @property
    def carry(self):
        """
        Return carry flag
        """
        return bool(self._flags & C_FLAG)

    @property
    def overflow(self):
        """
        Return overflow flag
        """
        return bool(self._flags & V_FLAG)

    def execute(self, a, b):
        """
        Execute operation with operands a and b. This will
        clear flags before operation, then call the function
        that we looked up in self._ops. It returns the result
        as signed to handle two's complement correctly.

        Do not change this method!
        """
        self._flags = 0  # clear flags before operation
        result = self._ops[self._op](a, b)  # type: ignore[operator]
        return self._to_signed(result)

    def _add(self, a, b):
        """
        ADD
        """
        a = a & WORD_MASK
        b = b & WORD_MASK
        result = (a + b) & WORD_MASK
        self._update_arith_flags_add(a, b, result)
        return result

    def _sub(self, a, b):
        """
        SUB
        """
        a = a & WORD_MASK
        b = b & WORD_MASK
        result = (a + (~b + 1)) & WORD_MASK
        self._update_arith_flags_sub(a, b, result)
        return result


    def _and(self, a, b):
        """
        Bitwise AND
        """
        a = a & WORD_MASK
        b = b & WORD_MASK
        result = (a & b) & WORD_MASK
        self._update_logic_flags(result)
        return result

    def _or(self, a, b):
        """
        Bitwise OR
        """
        a = a & WORD_MASK
        b = b & WORD_MASK
        result = a|b
        self._update_arith_flags_logic(self, result)
        return result

    def _xor(self, a, b):
        """
        Bitwise XOR
        """
        a = a & WORD_MASK
        b = b & WORD_MASK
        result = (a ^ b) & WORD_MASK
        self._update_logic_flags(result)
        return result

    def _shft(self, a, b):
        """
        SHFT

        shift left if MSB of B == 0, right otherwise; no shift if b = 0

        Keep in mind when we shift we need to keep track of the
        last bit shifted out. This is used to set the carry flag.
        """
        a &= WORD_MASK  # Keep this line as is

        if b == 0:
            result = a
        elif b & 0x8000: # shft right
            bit_out = (a & 0x1)
            result = a >> (b & 0xF)
        else: # shft left
            bit_out = (a & 0x8000)
            result = a << (b & 0xF)

        # Keep these last two lines as they are
        self._update_shift_flags(result, bit_out)
        return result

    def _to_signed(self, x):
        """
        Helper to convert unsigned to signed

        Do not modify this method!
        """
        if x & (1 << (WORD_SIZE - 1)):
            return x - (1 << WORD_SIZE)
        return x

    def _update_logic_flags(self, result):
        if result & (1 << (WORD_SIZE - 1)):
            self._flags |= N_FLAG
        if result == 0:
            self._flags |= Z_FLAG


    def _update_arith_flags_add(self, a, b, result):
        if result & (1 << (WORD_SIZE - 1)):
            self._flags |= N_FLAG
        if result == 0:
            self._flags |= Z_FLAG
        if a + b > WORD_MASK:
            self._flags |= C_FLAG
        sa, sb, sr = (
            (a >> (WORD_SIZE - 1)) & 1,
            (b >> (WORD_SIZE - 1)) & 1,
            (result >> (WORD_SIZE - 1)) & 1,
        )
        if sa == sb and sr != sa:
            self._flags |= V_FLAG

    def _update_arith_flags_sub(self, a, b, result):
        if result & (1 << (WORD_SIZE - 1)):
            self._flags |= N_FLAG
        if result == 0:
            self._flags |= Z_FLAG
        if a >= b:
            self._flags |= C_FLAG
        sa, sb, sr = (
            (a >> (WORD_SIZE - 1)) & 1,
            (b >> (WORD_SIZE - 1)) & 1,
            (result >> (WORD_SIZE - 1)) & 1,
        )
        if sa != sb and sr != sa:
            self._flags |= V_FLAG

    def _update_shift_flags(self, result, bit_out):
        if result & (1 << (WORD_SIZE - 1)):
            self._flags |= N_FLAG
        if bit_out != 0:
            self._flags |= C_FLAG
        if result == 0:
            self._flags |= Z_FLAG
