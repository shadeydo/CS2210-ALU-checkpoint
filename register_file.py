"""
Register file for the Catamount Processing Unit

In our Catamount Processing Unit we have eight general purpose registers.
R7 is reserved for use as stack pointer.
These do not include special-purpose registers elsewhere in the CPU:
  - instruction register, and
  - program counter.

CS 2210 Computer Organization
Clayton Cafiero <cbcafier@uvm.edu>

STARTER CODE - REPLACE THIS LINE WITH YOUR NAME HERE
"""

from constants import WORD_SIZE


class Register:
    """
    Class representing a single register.

    Registers understand their name, e.g., R0, R1, ..., etc. and the range
    of values they can store (and not much else).
    """

    MAX_VALUE = 2**WORD_SIZE - 1
    MIN_VALUE = -(2**WORD_SIZE)

    def __init__(self, name):
        self.name = name
        self.value = 0

    def read(self):
        # Just a getter for value. Replace `pass` below.
        pass

    def write(self, value):
        # Registers themselves don't know about write enable. It's the register
        # file that serves as gatekeeper in that regard. However, our registers
        # should reject values that are too wide (too many bits). Use class
        # constants here, and raise `ValueError` on bad value, otherwise set
        # the value field. Replace `pass` below.
        pass

    @property
    def raw(self):
        return self.value & 0xFFFF  # always unsigned

    def __repr__(self):
        return f"{self.raw:04X}"


class RegisterFile:
    """
    Two read ports, one write port register file, with the specified number
    of registers (8).
    """

    NUM_REGISTERS = 8

    def __init__(self):
        # When we instantiate our register file, we should instantiate eight
        # register objects and include them in a list `self.registers`. Note:
        # register objects should each get a unique name, R0, R1, R2, etc.
        # apart from their index in the list. Replace `pass` below.
        self.registers = ["FIX ME"]
        pass

    def _check_index(self, idx):
        """
        We cannot rely on Python's index out-of-bounds, because we don't want
        to permit negative indices (permitted by Python).
        """
        # Make sure `idx` is in the desired range, otherwise raise an
        # `IndexError` with message "Register index out of bounds!" This
        # method needn't have an explicit return. Replace `pass` below.
        pass

    def _read(self, ra, rb):
        """
        Read has been requested.

        Check bounds on `ra`, and check bounds on `rb` (if not None).

        Ensure source register(s) correctly specified. If `ra` and `rb` are
        both `None` raise `TypeError` with message: "Cannot read; no source
        register(s) specified!". If `rb` specified and not `ra`, raise
        `TypeError` with message: "Cannot read; single register read should
        specify `ra`!"

        If only `ra` is specified, return tuple: (value of `ra`, `None`).
        If both `ra` and `rb` are specified, return tuple: (value of `ra`,
        value of `rb`).

        """
        # Make sure that we have correct operand(s) to select register(s) from
        # which we'd like to read. Raise `TypeError` as needed. We have two
        # "good" scenarios: `ra` provided but `rb` is `None`, or both `ra` and
        # `rb` is specified. This method should call `_check_index()` as needed
        # to ensure we have valid indices. It should *always* return a tuple,
        # the first element of which is the value at `ra`, the second element
        # of which is the value at `rb` or `None`. Replace `pass` below.
        pass

    def _write(self, rd, data):
        """This is called if `write_enable` is `True`. This is how we detect
        that a write is intended. However, we need a destination and data for a
        successful write, so we have two failure modes (at this level):

            - `rd` is None
            - `data` is None

        Each of these should raise a `TypeError`. To simplify raising of
        exceptions, handle these in the order: bad `rd`, bad `data`.
        Messages should be:

            - "Cannot write; no destination specified!"
            - "Cannot write: no data!"

        respectively.

        Check bounds on `rd`.
        """
        # This code should only be reachable from `execute()`. `execute()` will
        # ensure that `write_enable` has been asserted. Accordingly, we need to
        # ensure that both `rd` and `data` are supplied. If either is `none`,
        # this method should raise a `TypeError`. If both are supplied, this
        # method should call `_check_index()` to ensure index is good. If so,
        # it should call `write()` on the appropriate register, as selected by
        # `rd`. Replace `pass` below.
        pass

    def execute(self, rd=None, ra=None, rb=None, data=None, write_enable=False):
        """
        `rd`: destination register (an `int`)
        `ra`: source register 1 (an `int`)
        `rb`: source register 2 (an `int`)
        `data`: data to write (an `int`)
        `write_enable`: `True` to enable write or `False`
        """
        if write_enable:
            self._write(rd, data)  # looks like a write
            return

        return self._read(ra, rb)  # looks like a read

    def __repr__(self):
        # Notice that this expects a member field `registers`, a list.
        vals = [str(r) for r in self.registers]
        return "\n".join(vals)


if __name__ == "__main__":
    # Quick smoke test...
    rf = RegisterFile()
    rf.execute(ra=0)
    rf.execute(rd=4, data=0xABCD, write_enable=True)

    print(rf)
