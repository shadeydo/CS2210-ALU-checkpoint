"""
Tests for memory classes

CS 2210 Computer Organization
Clayton Cafiero <cbcafier@uvm.edu>
"""

import pytest

from constants import STACK_BASE
from memory import DataMemory, InstructionMemory, Memory


def test_write_out_of_range():
    """
    Ensures that trying to write outside of memory range results in a
    `ValueError`.
    """
    m = Memory()
    m.write_enable(True)
    with pytest.raises(ValueError):
        m.write(0x10000, 0xABCD)  # beyond 16-bit range


@pytest.mark.parametrize(
    "addr,expected",
    [
        pytest.param(0x0000, 0x0000, id="addr=0x0000, expected=0x0000"),
        pytest.param(0x1234, 0x0000, id="addr=0x1234, expected=0x0000"),
        pytest.param(0xFFFF, 0x0000, id="addr=0xFFFF, expected=0x0000"),
        pytest.param(0xFEFF, 0x0000, id="addr=0xFEFF, expected=0x0000"),
    ],
)
def test_read_default_from_unwritten_cell(addr, expected):
    """
    Ensures we get 0x0 (default) when reading uninitialized memory cell.
    """
    m = Memory()
    assert m.read(addr) == expected


@pytest.mark.parametrize(
    "addr,val",
    [
        pytest.param(0x0000, 0xABCD, id="addr=0x0000, val=0xABCD"),
        pytest.param(0x0001, 0x1234, id="addr=0x0001, val=0x1234"),
        pytest.param(0x0002, 0x1111, id="addr=0x0002, val=0x1111"),
        pytest.param(0xFEFF, 0xDCBA, id="addr=0xFEFF, val=0xDCBA"),
    ],
)
def test_mem_write_when_enabled(addr, val):
    """Ensure that when enabled we do indeed write."""
    m = Memory()
    m.write_enable(True)
    m.write(addr, val)
    assert m.read(addr) == val


def test_mem_write_when_disabled():
    """
    Ensures when we try to write without previously asserting write enable,
    we get `RuntimeError`.
    """
    m = Memory()
    with pytest.raises(RuntimeError):
        m.write(0, 0xABCD)


def test_write_enable_rejects_non_bool():
    """
    Ensures write_enable() raises TypeError if passed a non-boolean.
    """
    m = Memory()
    with pytest.raises(TypeError):
        m.write_enable(1)


def test_write_enable_clears_after_write():
    """
    Ensures that immediately after write, memory automatically disables write.
    """
    m = Memory()
    m.write_enable(True)
    m.write(0x0000, 0xABCD)
    assert not m._write_enable


@pytest.mark.parametrize(
    "addr,val",
    [
        pytest.param(0x0000, 0xABCD, id="addr=0x0000, val=0xABCD"),
        pytest.param(0x0000, 0x1234, id="addr=0x0000, val=0x1234"),
    ],
)
def test_mem_hexdump(addr, val):
    # TODO:This is a feeble test---should revise.
    m = Memory()
    m.write_enable(True)
    m.write(addr, val)
    for line in m.hexdump(0, 1):
        addr_str = f"{addr:04X}"
        val_str = f"{val:04X}"
        assert line == f"{addr_str}: {val_str}"


def test_hexdump_multiple_lines_and_range():
    m = Memory()
    for i in range(10):
        m.write_enable(True)
        m.write(i, i)
    lines = list(m.hexdump(0, 10, width=4))
    assert len(lines) == 3  # restricted to width


def test_load_program():
    """
    Ensures instructions properly loaded in instruction memory.
    """
    p = [0x0DFF, 0xC002, 0xE000, 0x9206, 0x5288, 0xA003, 0xD000]
    im = InstructionMemory()
    im.load_program(p)
    for addr, inst in enumerate(p):
        assert im.read(addr) == inst


def test_load_program_disables_write():
    """
    Ensures that instruction memory is locked down after load.
    """
    im = InstructionMemory()
    im.load_program([0x1234])
    assert not im._write_enable


def test_instruction_memory_write_protected():
    """
    Ensures that instruction memory is locked down after load, and a
    `RuntimeError` is raised if we attempt write.
    """
    im = InstructionMemory()
    with pytest.raises(RuntimeError):
        im.write_enable(True)
        im.write(0x0000, 0xBEEF)


def test_instruction_memory_load_program_allowed():
    """
    Ensure that we can write once to instruction memory via `.load_program()`.
    """
    im = InstructionMemory()
    program = [0xAAAA, 0xBBBB]
    im.load_program(program)
    for addr, word in enumerate(program):
        assert im.read(addr) == word


def test_data_memory_stack_region_writable():
    """
    The stack region is ordinary data memory: programs keep locals and saved
    registers there, so plain writes at and above STACK_BASE must succeed.
    """
    dm = DataMemory()
    for addr, val in [(STACK_BASE, 0xABCD), (STACK_BASE + 1, 0xBEEF)]:
        dm.write_enable(True)
        dm.write(addr, val)
        assert dm.read(addr) == val


def test_data_memory_top_of_memory_writable():
    """
    The highest address (0xFFFF) can be written and read back.
    """
    dm = DataMemory()
    dm.write_enable(True)
    dm.write(0xFFFF, 0x1234)
    assert dm.read(0xFFFF) == 0x1234


def test_data_memory_normal_region_writable():
    """
    Writes below STACK_BASE should always succeed.
    """
    dm = DataMemory()
    dm.write_enable(True)
    dm.write(0x0100, 0x1234)
    assert dm.read(0x0100) == 0x1234


def test_memory_len_and_contains():
    """
    Ensure keys are added correctly in memory dictionary.
    """
    m = Memory()
    assert len(m) == 0
    m.write_enable(True)
    m.write(0, 0xABCD)
    assert len(m) == 1
    assert 0 in m
    assert 1 not in m
