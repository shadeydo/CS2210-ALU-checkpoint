"""
Tests for instruction set

CS 2210 Computer Organization
Clayton Cafiero <cbcafier@uvm.edu>
"""

import pytest

from instruction_set import (
    ISA,
    OPCODE_MAP,
    PSEUDO,
    Instruction,
    get_instruction_spec,
)


def test_get_instruction_spec_basic():
    assert get_instruction_spec("ADD")["opcode"] == 0x6
    assert get_instruction_spec("LOADI")["opcode"] == 0x1
    assert get_instruction_spec("HALT")["opcode"] == 0x0


_BCOND_MNEMS = {"BEQ", "BNE", "BLT", "BGE"}


def test_opcode_map_is_inverse_of_isa():
    for mnem, spec in OPCODE_MAP.items():
        assert isinstance(mnem, int)
        assert isinstance(spec, str)
    # round-trip check -- Bcond family shares opcode 0xC; OPCODE_MAP[0xC]
    # is one representative mnemonic from that family, which is fine.
    for mnem, info in ISA.items():
        code = info["opcode"]
        if mnem in _BCOND_MNEMS:
            assert OPCODE_MAP[code] in _BCOND_MNEMS
        else:
            assert OPCODE_MAP[code] == mnem


@pytest.mark.parametrize(
    "raw,mnem,expect",
    [
        (0x1000, "LOADI", {"rd": 0x0, "imm": 0x0, "zero": 0x0}),
        (0x1DFE, "LOADI", {"rd": 0x6, "imm": 0xFF, "zero": 0x0}),
        (0x26DE, "LUI", {"rd": 0x3, "imm": 0x6F, "zero": 0x0}),
        (0x357F, "LOAD", {"rd": 0x2, "ra": 0x5, "addr": 0x3F, "zero": 0x0}),
        (0x457F, "STORE", {"ra": 0x2, "rb": 0x5, "addr": 0x3F, "zero": 0x0}),
        (0xC040, "BEQ", {"imm": 0x04, "cc": 0b00, "zero": 0x0}),
        (0xCFA4, "BNE", {"imm": 0xFA, "cc": 0b01, "zero": 0x0}),
        (0xC208, "BLT", {"imm": 0x20, "cc": 0b10, "zero": 0x0}),
        (0xC20C, "BGE", {"imm": 0x20, "cc": 0b11, "zero": 0x0}),
        (0xD010, "B", {"imm": 0x10, "zero": 0x0}),
        (0x5E6B, "ADDI", {"rd": 0x7, "ra": 0x1, "imm": 0x2B}),
        (0x6488, "ADD", {"rd": 0x2, "ra": 0x2, "rb": 0x1, "zero": 0x0}),
        (0x7250, "SUB", {"rd": 0x1, "ra": 0x1, "rb": 0x2, "zero": 0x0}),
        (0x8650, "AND", {"rd": 0x3, "ra": 0x1, "rb": 0x2, "zero": 0x0}),
        (0x9AE0, "OR", {"rd": 0x5, "ra": 0x3, "rb": 0x4, "zero": 0x0}),
        (0xA650, "XOR", {"rd": 0x3, "ra": 0x1, "rb": 0x2, "zero": 0x0}),
        (0xB650, "SHFT", {"rd": 0x3, "ra": 0x1, "rb": 0x2, "zero": 0x0}),
        (0xE010, "CALL", {"imm": 0x01, "zero": 0x0}),
        (0xF000, "RET", {"zero": 0x000}),
        (0x0000, "HALT", {"zero": 0x000}),
    ],
)
def test_instruction_decoding(raw, mnem, expect):
    i = Instruction(raw=raw)
    assert i.mnem == mnem
    for field, val in expect.items():
        assert getattr(i, field) == val, (
            f"{mnem}.{field} expected {val:#x}, got {getattr(i, field):#x}"
        )


@pytest.mark.parametrize(
    "raw",
    [
        0x0001,  # HALT, low bit set
        0x1001,  # LOADI, padding bit set
        0x2001,  # LUI, padding bit set
        0x6489,  # ADD, padding bits set (R-format)
        0xB651,  # SHFT, padding bit set
        0xC041,  # BEQ, padding bit set (Bcond)
        0xD155,  # B, bits 11:8 set
        0xDF00,  # B, bits 11:8 set, imm = 0
        0xE011,  # CALL, padding bit set
        0xF001,  # RET, padding bit set
    ],
)
def test_nonzero_padding_rejected(raw):
    """
    Words whose zero-padding bits are not zero are malformed, in every
    format. Decoding must reject them rather than ignore the bits.
    """
    with pytest.raises(ValueError, match="padding"):
        Instruction(raw=raw)


def test_flags_field_consistent_with_alu():
    """
    Every ISA entry (and pseudo-instruction) declares which flags it sets.
    ALU instructions set at least N and Z; nothing else touches the flags.
    """
    for table in (ISA, PSEUDO):
        for mnem, info in table.items():
            flags = info["flags"]
            assert set(flags) <= set("NZCV"), mnem
            if info["alu"]:
                assert {"N", "Z"} <= set(flags), mnem
            else:
                assert flags == "", mnem
    assert PSEUDO["MOV"]["flags"] == ISA["ADDI"]["flags"]


def test_repr_contains_fields():
    i = Instruction(raw=0x5E6B)  # ADDI example
    s = repr(i)
    assert "ADDI" in s
    assert "raw_hex=" in s
    assert "raw_bin=" in s
