"""
Tests for Register and RegisterFile classes

CS 2210 Computer Organization
Clayton Cafiero <cbcafier@uvm.edu>
"""

import pytest

from register_file import Register, RegisterFile


# parametrize allows us to list multiple test paramters and have these
# injected into individual tests. This runs two separate tests, one on
# `Register.MAX_VALUE + 1` and another on `Register.MIN_VALUE - 1`.
@pytest.mark.parametrize("value", [Register.MAX_VALUE + 1, Register.MIN_VALUE - 1])
def test_reject_data_out_of_bounds(value):
    """
    Ensure bad values are rejected.
    """
    with pytest.raises(ValueError):
        # This creates a context for handling tests we _expect_ should
        # raise an exception. This context manager handles all the
        # `try`, `except`, and `finally` so we can focus on tests.
        r = Register("R0")
        r.write(value)


@pytest.mark.parametrize(
    "value",
    [
        Register.MIN_VALUE,
        Register.MIN_VALUE + 1,
        -42,
        -1,
        0,
        1,
        2,
        42,
        Register.MAX_VALUE,
        Register.MAX_VALUE - 1,
    ],
)
def test_read_write_data(value):
    """
    Make sure that if we write something, we get the same value back.
    """
    r = Register("R0")
    r.write(value)
    assert r.read() == value


def test_read_write_rf():
    """
    Make sure that if we write something via register file, we get the same
    value back on a read.
    """
    rf = RegisterFile()
    rf.execute(rd=0, data=77, write_enable=True)
    assert rf.execute(ra=0) == (77, None)
    rf.execute(rd=7, data=77, write_enable=True)
    assert rf.execute(ra=7) == (77, None)


def test_read_tuple():
    rf = RegisterFile()
    rf.execute(rd=0, data=77, write_enable=True)
    assert rf.execute(ra=0) == (77, None)
    rf.execute(rd=7, data=42, write_enable=True)
    assert rf.execute(ra=7) == (42, None)
    assert rf.execute(ra=0, rb=7) == (77, 42)


def test_error_on_write_no_destination():
    """
    Make sure register file rejects bad destination on write (default is
    `None`, hence `TypeError`).
    """
    rf = RegisterFile()
    with pytest.raises(TypeError, match="no destination specified"):
        rf.execute(data=77, write_enable=True)  # no destination


def test_error_on_write_no_data():
    """
    Make sure register file rejects bad data on write (default is `None`,
    hence `TypeError`).
    """
    rf = RegisterFile()
    with pytest.raises(TypeError, match="no data"):
        rf.execute(rd=1, write_enable=True)  # no data


def test_error_on_read_no_args():
    """
    Make sure register file raises TypeError when no source register specified.
    """
    rf = RegisterFile()
    with pytest.raises(TypeError, match="no source register"):
        rf.execute()


def test_error_on_read_rb_only():
    """
    Make sure register file raises TypeError when rb is given but not ra.
    """
    rf = RegisterFile()
    with pytest.raises(TypeError, match="specify `ra`"):
        rf.execute(rb=0)


oob_read_tests = [
    pytest.param({"ra": 0, "rb": 8}, id="ra=0, rb=8"),
    pytest.param({"ra": 8, "rb": 0}, id="ra=8, rb=0"),
    pytest.param({"ra": 8, "rb": 8}, id="ra=8, rb=8"),
    pytest.param({"ra": -1}, id="ra=-1"),
    pytest.param({"ra": 0x10000}, id="ra=0X10000"),
    pytest.param({"ra": -2}, id="ra=-2"),
    pytest.param({"ra": -8}, id="ra=-8"),
    pytest.param({"ra": 8}, id="ra=8"),
    pytest.param({"ra": -1, "rb": 0}, id="ra=-1, rb=0"),
    pytest.param({"ra": 0, "rb": -1}, id="ra=0, rb=-1"),
]


@pytest.mark.parametrize("args", oob_read_tests)
def test_index_out_of_bounds_read(args):
    """
    Make sure we reject indices too large or negative (on read).
    """
    rf = RegisterFile()
    with pytest.raises(IndexError, match="Register index out of bounds!"):
        # If you've not seen `**` before, it's a Python "splat", which
        # unpacks a dictionary into keyword arguments.
        rf.execute(**args)


oob_write_tests = [
    pytest.param(
        {"rd": 8, "data": 77, "write_enable": True},
        id="rd=8, data=77, write_enable=True",
    ),
    pytest.param(
        {"rd": -1, "data": 77, "write_enable": True},
        id="rd=-1, data=77, write_enable=True",
    ),
]


@pytest.mark.parametrize("args", oob_write_tests)
def test_index_out_of_bounds_write(args):
    """
    Make sure we reject indices too large or negative (on write).
    """
    rf = RegisterFile()
    with pytest.raises(IndexError, match="Register index out of bounds!"):
        rf.execute(**args)


def test_two_register_read_order():
    """
    Make sure arguments are handled in correct order.
    """
    rf = RegisterFile()
    rf.execute(rd=1, data=0x1234, write_enable=True)
    rf.execute(rd=2, data=0xABCD, write_enable=True)
    assert rf.execute(ra=1) == (0x1234, None)
    assert rf.execute(ra=1, rb=2) == (0x1234, 0xABCD)


def test_two_register_alias():
    """
    Make sure we get correct value if `ra` and `rb` are same register.
    """
    rf = RegisterFile()
    rf.execute(rd=1, data=0x1234, write_enable=True)
    rf.execute(rd=2, data=0xABCD, write_enable=True)
    assert rf.execute(ra=2, rb=2) == (0xABCD, 0xABCD)


def test_extraneous_read_args_are_ignored_on_write():
    """
    Make sure extraneous arguments ignored on write.
    """
    rf = RegisterFile()
    # ra, rb should be ignored
    rf.execute(rd=3, data=77, write_enable=True, ra=1, rb=2)
    assert rf.execute(ra=3) == (77, None)


def test_extraneous_write_args_are_ignored_on_read():
    """
    Make sure extraneous arguments ignored on read.
    """
    rf = RegisterFile()
    rf.execute(rd=1, data=77, write_enable=True)
    rf.execute(rd=5, data=42, write_enable=True)
    # rd, data should be ignored
    rf.execute(rd=3, data=77, write_enable=False, ra=1, rb=5)
    assert rf.execute(ra=1) == (77, None)
    assert rf.execute(ra=1, rb=5) == (77, 42)
