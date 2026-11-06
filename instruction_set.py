"""
Instruction set for Catamount Processing Unit (CPU)

The Catamount Processing Unit (CPU) has a 16-bit address space and 
word size, with  word-aligned accesses, signed-offset addressing, and 
a linear memory  model where all effective-address computations happen 
in 16-bit two's-complement arithmetic. Like a Harvard architecture, it
has separate memory for program and data
CS 2210 Computer Organization
Clayton Cafiero <cbcafier@uvm.edu>

Address arithmetic
------------------
Effective addresses (LOAD, STORE) and the program counter (fetch, branches,
CALL) are computed modulo 2^16. A register holding -1 and one holding 0xFFFF
are the same address; 0xFFFF + 1 wraps to 0x0000; and a branch back past
address 0 lands near the top of instruction memory.

The stack
---------
The stack pointer, SP, is R7. This is architectural, not a convention:
CALL and RET use R7 implicitly, so no program should use R7 for anything
else. At reset, R7 = 0xFFFF (STACK_TOP), which means the stack is empty. 
The stack grows downward through ordinary data memory: CALL decrements R7 
and writes the return address at MEM[R7]; RET reads MEM[R7] and increments 
R7. The stack occupies 0xFF00 to 0xFFFE (255 words; 0xFFFF is never written).
CALL raises an error if the stack would grow below 0xFF00, and RET raises 
one if R7 is already 0xFFFF. CALL and RET adjust R7 without using the ALU, 
so they leave the flags alone.

The stack is not protected: LOAD and STORE can reach it like any other
memory, which is how programs build stack frames. A subroutine allocates a
frame with ADDI R7, R7, #-n, reaches its locals and saved registers with
[R7 + #k] (k in 0..31), and frees the frame with ADDI R7, R7, #n before RET.
(ADDI is an ALU instruction, so it sets the flags.) The R7 + offset addressing
mode needs no frame pointer as long as frame sizes are fixed.

Flags
-----
The N, Z, C, and V flags are implicit state, not an operand. Every ALU
instruction (ADD, SUB, ADDI, AND, OR, XOR, SHFT, and the pseudo-instruction
MOV Rd, Ra, which is ADDI) overwrites all four flags. No other instruction
(LOADI, LUI, LOAD, STORE, branches, CALL, RET, and MOV Rd, #imm, which is
LOADI or LOADI + LUI) touches them. A conditional branch
tests whatever the most recent ALU instruction left behind, so the compare
and the branch should be adjacent: a MOV or ADDI in between silently changes
what the branch sees. To compare without keeping the result, SUB into a
scratch register (e.g., SUB R5, R4, R2) and branch immediately.

v. 2.3.0 2026-10-08
    See CHANGELOG.md for the full version history.
"""

from dataclasses import dataclass  # For Instruction class, below.

# Instruction set specification
#
# "flags" lists the status flags (N, Z, C, V) an instruction can set. Flags
# are implicit global state: every ALU instruction (alu=True) overwrites ALL
# four flags, setting those listed and clearing the rest; every other
# instruction ("flags" is empty) leaves them untouched. Branches read the
# flags left by the most recent ALU instruction. See "Flags" in the module
# docstring.
ISA = {
    "HALT": {
        "opcode": 0x0,
        "format": "O",
        "variant": "halt",
        "fields": ["opcode(4)", "zero(12)"],
        "semantics": "stop execution",
        "description": "Halt CPU.",
        "register_write": False,
        "memory_write": False,
        "alu": False,
        "flags": "",
        "immediate": False,
        "branch": False,
    },
    "LOADI": {
        "opcode": 0x1,
        "format": "I",
        "variant": "imm-only",
        "fields": ["opcode(4)", "rd(3)", "imm(8)", "zero(1)"],
        "semantics": "Rd <-- imm8 (zero-extended)",
        "description": "Load immediate 8-bit constant into Rd.",
        "register_write": True,
        "memory_write": False,
        "alu": False,
        "flags": "",
        "immediate": True,
        "branch": False,
    },
    "LUI": {
        "opcode": 0x2,
        "format": "I",
        "variant": "imm-only",
        "fields": ["opcode(4)", "rd(3)", "imm(8)", "zero(1)"],
        "semantics": "Rd[15:8] <-- imm8 (leaves Rd[7:0] unchanged)",
        "description": "Load immediate into upper byte of Rd.",
        "register_write": True,
        "memory_write": False,
        "alu": False,
        "flags": "",
        "immediate": True,
        "branch": False,
    },
    "LOAD": {
        "opcode": 0x3,
        "format": "M",
        "fields": ["opcode(4)", "rd(3)", "ra(3)", "addr(6)"],
        "semantics": "Rd <-- MEM[(Ra + signextend(addr6)) mod 2^16]",
        "description": "Load word from memory at [Ra + offset] into Rd.",
        "register_write": True,
        "memory_write": False,
        "alu": False,  # assume aux adder for eff address
        "flags": "",
        "immediate": False,
        "branch": False,
    },
    "STORE": {
        "opcode": 0x4,
        "format": "M",
        "fields": ["opcode(4)", "ra(3)", "rb(3)", "addr(6)"],
        "semantics": "MEM[(Rb + signextend(addr6)) mod 2^16] <-- Ra",
        "description": "Store Ra (data source) to memory at Rb (base) + offset.",
        "register_write": False,
        "memory_write": True,
        "alu": False,  # assume aux adder for eff address
        "flags": "",
        "immediate": False,
        "branch": False,
    },
    "ADDI": {
        "opcode": 0x5,
        "format": "I",
        "variant": "reg+imm",
        "fields": ["opcode(4)", "rd(3)", "ra(3)", "imm(6)"],
        "semantics": "Rd <-- Ra + signextend(imm6)",
        "description": "Add signed 6-bit immediate value to Ra.",
        "register_write": True,
        "memory_write": False,
        "alu": True,
        "flags": "NZCV",
        "immediate": True,
        "branch": False,
    },
    "ADD": {
        "opcode": 0x6,
        "format": "R",
        "fields": ["opcode(4)", "rd(3)", "ra(3)", "rb(3)", "zero(3)"],
        "semantics": "Rd <-- Ra + Rb",
        "description": "Add values in two registers.",
        "register_write": True,
        "memory_write": False,
        "alu": True,
        "flags": "NZCV",
        "immediate": False,
        "branch": False,
    },
    "SUB": {
        "opcode": 0x7,
        "format": "R",
        "fields": ["opcode(4)", "rd(3)", "ra(3)", "rb(3)", "zero(3)"],
        "semantics": "Rd <-- Ra - Rb",
        "description": "Subtract value in Rb from value in Ra.",
        "register_write": True,
        "memory_write": False,
        "alu": True,
        "flags": "NZCV",
        "immediate": False,
        "branch": False,
    },
    "AND": {
        "opcode": 0x8,
        "format": "R",
        "fields": ["opcode(4)", "rd(3)", "ra(3)", "rb(3)", "zero(3)"],
        "semantics": "Rd <-- Ra & Rb",
        "description": "Bitwise AND of two registers.",
        "register_write": True,
        "memory_write": False,
        "alu": True,
        "flags": "NZ",
        "immediate": False,
        "branch": False,
    },
    "OR": {
        "opcode": 0x9,
        "format": "R",
        "fields": ["opcode(4)", "rd(3)", "ra(3)", "rb(3)", "zero(3)"],
        "semantics": "Rd <-- Ra | Rb",
        "description": "Bitwise OR of two registers.",
        "register_write": True,
        "memory_write": False,
        "alu": True,
        "flags": "NZ",
        "immediate": False,
        "branch": False,
    },
    "XOR": {
        "opcode": 0xA,
        "format": "R",
        "fields": ["opcode(4)", "rd(3)", "ra(3)", "rb(3)", "zero(3)"],
        "semantics": "Rd <-- Ra ^ Rb",
        "description": "Bitwise XOR of two registers.",
        "register_write": True,
        "memory_write": False,
        "alu": True,
        "flags": "NZ",
        "immediate": False,
        "branch": False,
    },
    "SHFT": {
        "opcode": 0xB,
        "format": "R",
        "fields": ["opcode(4)", "rd(3)", "ra(3)", "rb(3)", "zero(3)"],
        "semantics": "if Rb & 0x8000: Rd <-- Ra >> (Rb & 0xF) "
        "else Rd <-- Ra << (Rb & 0xF)",
        "description": "Logical shift left or right depending on MSB of Rb. "
        "Absolute value of shift amount is limited to 15. "
        "We use the MSB of Rb to indicate direction of the shift."
        "If MSB is zero, then left shift; otherwise, right shift."
        "We use the lowest four bits of Rb for shift amount.",
        "register_write": True,
        "memory_write": False,
        "alu": True,
        "flags": "NZC",
        "immediate": False,
        "branch": False,
    },
    # Bcond family: all share opcode 0xC, distinguished by cc field in bits [3:2].
    # Encoding: opcode(4) | imm(8) | cc(2) | zero(2)
    # OPCODE_MAP[0xC] resolves to "BGE" (last defined); _decode_from_word
    # overrides self.mnem using the cc field to yield the specific mnemonic.
    "BEQ": {
        "opcode": 0xC,
        "cc": 0b00,
        "format": "B",
        "variant": "cond",
        "fields": ["opcode(4)", "imm(8)", "cc(2)", "zero(2)"],
        "semantics": "if Z == 1: PC <-- PC + signextend(imm8)",
        "description": "Branch if zero flag is set (cc=00). "
        "Branch offset is PC-relative to the instruction after the branch.",
        "register_write": False,
        "memory_write": False,
        "alu": False,
        "flags": "",
        "immediate": True,
        "branch": True,
    },
    "BNE": {
        "opcode": 0xC,
        "cc": 0b01,
        "format": "B",
        "variant": "cond",
        "fields": ["opcode(4)", "imm(8)", "cc(2)", "zero(2)"],
        "semantics": "if Z == 0: PC <-- PC + signextend(imm8)",
        "description": "Branch if zero flag is clear (cc=01). "
        "Branch offset is PC-relative to the instruction after the branch.",
        "register_write": False,
        "memory_write": False,
        "alu": False,
        "flags": "",
        "immediate": True,
        "branch": True,
    },
    "BLT": {
        "opcode": 0xC,
        "cc": 0b10,
        "format": "B",
        "variant": "cond",
        "fields": ["opcode(4)", "imm(8)", "cc(2)", "zero(2)"],
        "semantics": "if N != V: PC <-- PC + signextend(imm8)",
        "description": "Branch if signed less-than, i.e., N and V differ "
        "(cc=10). After SUB Ra, Rb this means Ra < Rb as signed values, "
        "even when the subtraction overflows. "
        "Branch offset is PC-relative to the instruction after the branch.",
        "register_write": False,
        "memory_write": False,
        "alu": False,
        "flags": "",
        "immediate": True,
        "branch": True,
    },
    "BGE": {
        "opcode": 0xC,
        "cc": 0b11,
        "format": "B",
        "variant": "cond",
        "fields": ["opcode(4)", "imm(8)", "cc(2)", "zero(2)"],
        "semantics": "if N == V: PC <-- PC + signextend(imm8)",
        "description": "Branch if signed greater-or-equal, i.e., N and V agree "
        "(cc=11). After SUB Ra, Rb this means Ra >= Rb as signed values, "
        "even when the subtraction overflows. "
        "Branch offset is PC-relative to the instruction after the branch.",
        "register_write": False,
        "memory_write": False,
        "alu": False,
        "flags": "",
        "immediate": True,
        "branch": True,
    },
    "B": {
        "opcode": 0xD,
        "format": "B",
        "variant": "uncond",
        "fields": ["opcode(4)", "zero(4)", "imm(8)"],
        "semantics": "PC <-- PC + signextend(imm8)",
        "description": "Unconditional branch by signed 8-bit PC-relative "
        "offset. Branches apply this operation to PC after fetch, not PC "
        "before fetch. Branch offsets are PC-relative to the instruction "
        "after the branch (PC after fetch). imm8 is offset.",
        "register_write": False,  # writes directly to PC, not GP register
        "memory_write": False,
        "alu": False,
        "flags": "",
        "immediate": True,
        "branch": True,
    },
    "CALL": {
        "opcode": 0xE,
        "format": "B",
        "variant": "link",
        "fields": ["opcode(4)", "imm(8)", "zero(4)"],
        "semantics": "SP <-- SP - 1; MEM[SP] <-- PC (after fetch); "
        "PC <-- PC (after fetch) + signextend(imm8). SP is R7.",
        "description": "Call subroutine at address given by PC after fetch "
        "plus the signed 8-bit immediate. During fetch, PC is incremented. "
        "During execute, CALL decrements the stack pointer (R7), pushes the "
        "PC value after fetch (the return address) at the new top of stack, "
        "then jumps to the PC-relative target. Raises an error if the stack "
        "would grow below 0xFF00 (stack overflow). Does not affect the flags.",
        "register_write": True,  # writes SP (R7); PC is written directly
        "memory_write": True,  # pushes return address onto stack
        "alu": False,  # assume aux adder for increment
        "flags": "",
        "immediate": True,  # offset
        "branch": True,
    },
    "RET": {
        "opcode": 0xF,
        "format": "B",
        "variant": "ret",
        "fields": ["opcode(4)", "zero(12)"],
        "semantics": "PC <-- MEM[SP]; SP <-- SP + 1. SP is R7.",
        "description": "Return from subroutine: pop the return address at "
        "the top of the stack (R7) into PC, then increment R7. Raises an "
        "error if the stack is empty (stack underflow). Does not affect the "
        "flags. The 12 zero bits are reserved for future use.",
        "register_write": True,  # writes SP (R7); PC is written directly
        "memory_write": False,
        "alu": False,
        "flags": "",
        "immediate": False,
        "branch": True,
    },
}


# Pseudo-instructions: assembler-only; no opcode of their own.
# Same field structure as ISA entries where applicable; no opcode/format.
PSEUDO = {
    "MOV": {
        "expands_to": "ADDI Rd, Ra, #0",
        "fields": ["rd(3)", "ra(3)"],
        "semantics": "Rd <-- Ra",
        "description": "Copy register Ra into Rd (MOV Rd, Ra). "
        "Pseudo-instruction; assembles as ADDI Rd, Ra, #0. "
        "The assembler selects this form when the source operand is not "
        "prefixed with '#'; see MOV_IMM for the immediate form.",
        "register_write": True,
        "memory_write": False,
        "alu": True,
        "flags": "NZCV",  # expands to ADDI, so it clobbers the flags
        "immediate": False,
        "branch": False,
    },
    "MOV_IMM": {
        "expands_to": "LOADI Rd, #imm (imm <= 255); "
        "LOADI Rd, #lo8 + LUI Rd, #hi8 (otherwise)",
        "fields": ["rd(3)", "imm(16)"],
        "semantics": "Rd <-- imm16",
        "description": "Load a 16-bit constant into Rd (MOV Rd, #imm; imm "
        "in -32768..65535, negative values taken as two's complement). "
        "The assembler selects this form when the source operand starts "
        "with '#'. A value in 0..255 assembles to one word (LOADI); any "
        "other value assembles to two (LOADI for the low byte, then LUI "
        "for the high byte). Unlike the register form, this uses no ALU "
        "and leaves the flags untouched.",
        "register_write": True,
        "memory_write": False,
        "alu": False,
        "flags": "",
        "immediate": True,
        "branch": False,
    },
}


# Reverse map for opcode lookup
OPCODE_MAP = {v["opcode"]: k for k, v in ISA.items()}

# Condition code --> mnemonic for Bcond family
_CC_TO_MNEM = {0b00: "BEQ", 0b01: "BNE", 0b10: "BLT", 0b11: "BGE"}


def get_instruction_spec(key):
    """
    Helper function. Returns the ISA specification for a
    given mnemonic (str) or opcode (int).
    """
    if isinstance(key, str):
        return ISA[key.upper()]
    return ISA[OPCODE_MAP[key]]  # if it's not a str, assume it's an int


@dataclass
class Instruction:  # pylint: disable=too-many-instance-attributes
    """
    Represents a single decoded instruction for the Catamount
    Processing Unit (CPU).

    Fields correspond to the 16-bit ISA specification.

    We use Python dataclass for minimal, lightweight classes,
    almost like structs in C. When we instantiate an instruction,
    `i`, we can access its fields using dot notation, like this:

    i.opcode       # gets us the opcode of instruction i
    i.rd           # gets us the destination register of instruction i
    etc.
    """

    # Defaults (constructor is implicit)
    opcode: int = 0
    mnem: str = ""
    rd: int = 0
    ra: int = 0
    rb: int = 0
    imm: int = 0
    cc: int = 0  # condition code for Bcond family (BEQ/BNE/BLT/BGE)
    addr: int = 0
    zero: int = 0
    raw: int | None = None

    def __post_init__(self):
        """
        This is called immediately after the object is instantiated.
        If raw bytes have been provided, the instruction is auto-
        decoded. If not, then we assume all necessary fields have
        been supplied to the constructor.
        """
        if self.raw is not None:
            self._decode_from_word(self.raw)
        if not self.mnem and self.opcode:
            self.mnem = OPCODE_MAP.get(self.opcode, "???")
        if not self.opcode and self.mnem:
            self.opcode = ISA[self.mnem]["opcode"]

    @property
    def format(self):
        """
        Get the instruction format.
        """
        spec = ISA.get(self.mnem)
        if not spec:
            return None
        return spec["format"]

    def _decode_from_word(self, word):
        """
        Self-decode instruction from 16-bit word.
        """
        self.opcode = (word >> 12) & 0xF
        self.mnem = OPCODE_MAP.get(self.opcode, "???")
        fmt = self.format
        if fmt == "R":
            self.rd = (word >> 9) & 0x7
            self.ra = (word >> 6) & 0x7
            self.rb = (word >> 3) & 0x7
            self.zero = word & 0x7  # 3-bit zero padding
        elif self.mnem in ("LOADI", "LUI"):
            self.rd = (word >> 9) & 0x7
            self.imm = (word >> 1) & 0xFF
            self.zero = word & 1  # 1-bit zero padding
        elif self.mnem == "ADDI":
            self.rd = (word >> 9) & 0x7
            self.ra = (word >> 6) & 0x7
            self.imm = word & 0x3F
            self.zero = 0  # no zero padding
        elif fmt == "M":
            if self.mnem == "STORE":
                self.ra = (word >> 9) & 0x7  # source/data register
                self.rb = (word >> 6) & 0x7  # base register
            else:  # LOAD
                self.rd = (word >> 9) & 0x7  # destination register
                self.ra = (word >> 6) & 0x7  # base register
            self.addr = word & 0x3F  # 63 (6 bits)
            self.zero = 0  # no zero padding
        elif self.mnem == "CALL":
            self.imm = (word >> 4) & 0xFF
            self.zero = word & 0xF  # 4-bit zero padding
        elif self.mnem in ("RET", "HALT"):
            self.zero = word & 0xFFF  # 12-bit zero padding
        elif self.mnem in ("BEQ", "BNE", "BLT", "BGE"):
            self.imm = (word >> 4) & 0xFF
            self.cc = (word >> 2) & 0x3
            self.zero = word & 0x3
            self.mnem = _CC_TO_MNEM[self.cc]
        elif fmt == "B":  # B (unconditional): opcode(4) | zero(4) | imm(8)
            self.zero = (word >> 8) & 0xF  # 4-bit zero padding
            self.imm = word & 0xFF
        else:
            raise ValueError(f"Unhandled instruction {self.mnem}")
        self.raw = word
        if self.zero != 0:
            raise ValueError(
                f"Nonzero padding on {self.mnem}: "
                f"raw=0x{word:04X} (0b{word:016b}), zero=0x{self.zero:X}. "
                "Problem with decoding? Or assembler bug?"
            )

    @property
    def raw_bin(self):
        """
        Return pretty, zero padded binary representation of raw bytes.
        """
        assert self.raw is not None
        return "0b" + bin(self.raw)[2:].zfill(16)

    @property
    def raw_hex(self):
        """
        Return pretty, zero padded, upper-case hex representation of raw bytes.
        """
        assert self.raw is not None
        return "0x" + hex(self.raw)[2:].zfill(4).upper()

    def __repr__(self):
        """
        Revised 2025-11-01 to include raw bytes and conditional
        formatting by opcode, and to format fields as hex.
        """
        s = f"Instruction({self.mnem} (opcode={self.opcode}): "
        fmt = self.format
        if fmt is None:
            raise ValueError("Instruction format unknown")
        if fmt == "R":
            s += (
                f"rd=0x{self.rd:01X}, ra=0x{self.ra:01X}, "
                f"rb=0x{self.rb:01X}, zero={self.zero:01X}, "
            )
        elif self.mnem in ("LOADI", "LUI"):
            s += f"rd=0x{self.rd:01X}, imm=0x{self.imm:02X}, zero=0x{self.zero:01X}, "
        elif self.mnem == "ADDI":
            s += f"rd=0x{self.rd:01X}, ra=0x{self.ra:01X}, imm=0x{self.imm:02X}, "
        elif self.mnem == "LOAD":
            s += f"rd=0x{self.rd:01X}, ra=0x{self.ra:01X}, addr=0x{self.addr:03X}, "
        elif self.mnem == "STORE":
            s += f"ra=0x{self.ra:01X}, rb=0x{self.rb:01X}, addr=0x{self.addr:03X}, "
        elif self.mnem == "CALL":
            s += f"imm=0x{self.imm:02X}, zero=0x{self.zero:01X}, "
        elif self.mnem in ("RET", "HALT"):
            s += f"zero=0x{self.zero:03X}, "
        elif self.mnem in ("BEQ", "BNE", "BLT", "BGE"):
            s += f"imm=0x{self.imm:02X}, cc=0b{self.cc:02b}, zero=0x{self.zero:01X}, "
        elif fmt == "B":
            s += f"imm=0x{self.imm:02X}, zero=0x{self.zero:01X}, "
        s += f"raw_hex={self.raw_hex}, raw_bin={self.raw_bin})"
        return s
