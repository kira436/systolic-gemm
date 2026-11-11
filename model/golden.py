"""Golden (bit-accurate) reference models. Keep these in lockstep with the RTL contract in README.md."""
from dataclasses import dataclass
import numpy as np


def wrap(v: int, bits: int) -> int:
    """Wrap an integer to a signed two's-complement value of `bits` width.

    Python integers have unlimited width (they never overflow), so this function
    imitates what a fixed-width hardware register does: keep only the low `bits`
    bits, then read them back as a signed number.

    Verilog equivalent (for bits = 8):
        wire [7:0]        low  = v[7:0];   // truncate
        wire signed [7:0] out  = low;      // reinterpret as signed

    Worked example, wrap(200, 8):
        200            = 0b1100_1000
        mask           = 0b1111_1111   -> v stays 0b1100_1000 (200)
        top bit (bit7) = 1             -> negative, so 200 - 256 = -56
    """
    # (1 << bits)      : shift 1 left by `bits` places = 2**bits.  For bits=8: 0b1_0000_0000 (256)
    # (1 << bits) - 1  : all-ones mask of width `bits`.             For bits=8: 0b1111_1111   (255)
    # v &= mask        : shorthand for  v = v & mask  (bitwise AND, like `v = v & 8'hFF` in Verilog).
    #                    This keeps the low `bits` bits and zeroes everything above them,
    #                    i.e. truncation.  Result is always in 0 .. 2**bits - 1 (unsigned view).
    #                    Works for negative inputs too: Python treats negatives as infinitely
    #                    sign-extended two's complement, so wrap(-1, 8) -> v = 255 here.
    v &= (1 << bits) - 1

    # v >> (bits - 1)  : shift right so only the top (sign) bit is left, giving 0 or 1.
    #                    For bits=8 this is bit 7, i.e. v[7] in Verilog.
    # `X if cond else Y` is Python's version of the ternary operator `cond ? X : Y`.
    #   sign bit = 1 -> the value is negative in two's complement: subtract 2**bits
    #                   (e.g. 255 - 256 = -1, 200 - 256 = -56, 128 - 256 = -128)
    #   sign bit = 0 -> the value is already a non-negative number: return as is
    return v - (1 << bits) if v >> (bits - 1) else v


def gemm_int8(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """C = A @ B with INT8 inputs and INT32 accumulation (wraps like hardware would; no saturation)."""
    # assert: stop with an error if the condition is false (like a SystemVerilog immediate assert).
    # .dtype is the element type of a numpy array; here both inputs must be signed 8-bit.
    assert A.dtype == np.int8 and B.dtype == np.int8
    # .astype(np.int64) copies the array widened to 64-bit, so the multiply/add can't overflow.
    # `@` is the matrix-multiply operator (C[i][j] = sum over k of A[i][k] * B[k][j]).
    C = A.astype(np.int64) @ B.astype(np.int64)
    # lambda x: ...      : a small unnamed function, here "take x and wrap it to 32 bits".
    # np.vectorize(f)(C) : apply that function to every element of C.
    # .astype(np.int32)  : store the (already wrapped) results as 32-bit integers.
    return np.vectorize(lambda x: wrap(int(x), 32))(C).astype(np.int32)


# @dataclass auto-generates the boilerplate for a plain record type, similar to a
# SystemVerilog `struct`. Each field below is one PE register with its reset value (0).
@dataclass
class PEState:
    weight: int = 0
    a_out: int = 0
    psum_out: int = 0


def pe_step(s: PEState, load_w: int, w_in: int, a_in: int, psum_in: int) -> PEState:
    """One clock edge of a weight-stationary PE. Contract (change deliberately; update RTL + README too):
      - load_w=1: weight <= w_in; psum_out <= psum_in (no MAC that cycle)
      - load_w=0: psum_out <= psum_in + a_in * weight (32-bit wrap)
      - a_out <= a_in every cycle (activation passes east)

    `s` holds the register values *before* the clock edge; the returned PEState holds the
    values *after* it. Building a fresh PEState means every field updates at once, like
    non-blocking (<=) assignments inside one always_ff block.
    """
    if load_w:
        return PEState(weight=wrap(w_in, 8), a_out=wrap(a_in, 8), psum_out=wrap(psum_in, 32))
    return PEState(weight=s.weight, a_out=wrap(a_in, 8),
                   psum_out=wrap(psum_in + wrap(a_in, 8) * s.weight, 32))
